#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
# import hashlib
import json
import re
import sqlite3
import sys
from enum import Enum, Flag, auto
from pathlib import Path

import random
from time import sleep

import httpx #wrap with a try/except: import httpx as http
from rich import print
from sentinel.helpers import PathHelper
from sentinel.helpers import LogHelper
from sentinel.classes.Y3MasterDatabase import Y3MasterDatabase
from sentinel.classes.Y3AssetBundleReader import Y3AssetBundleReader
import Y3gk
# from .libgk.gkcrypt import gk

#TODO: should also try to support switching to iOS (and maybe.. but probably not WebGL) for tryhard max quality asset finding

class ResourceTypes(Flag):
    NULL = 0
    ASSET_BUNDLE = auto()
    MASTER_DATA = auto()
    SOUND = auto()

class APIEndpoints(Enum):

    def __str__(self):
        return f"http://app.yuyuyui.jp/api/v1{self.value}"

    requirement_version = "/requirement_version"
    resource_versions = "/resource_versions/{0}"
    sessions = "/sessions"

class Y3APISession:
    """A class that encapsulates methods for yuyuyui API including download
    handling and gk encryption/decryption.
    
    Play nice, or you'll be erased by the Taisha.
    """
    def __init__(self, app_version: str, uuid: str, username: str, password: str, gk_api_key: str, gk_asset_iv: str):
        """Set ``verbose_logging`` to show api calls while running.
        """
        self.logger = LogHelper.new_logger("sentinel.[green]y3apisession[/green]")
        self.uuid = uuid
        self.api_crypter = Y3gk.Igarashi(key=gk_api_key)
        self.asset_crypter = Y3gk.Takeshi(iv=bytes.fromhex(gk_asset_iv))
        self.required_update = None
        self.update_str = None
        self.resource_types = ResourceTypes.NULL
        self.current_vlist_version = None
        self.server_vlist_version = None
        self.session = httpx.Client(
            auth=(username, password),
            headers={
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; SM-G955N Build/NRD90M)", #TODO: implement as arg?
                        "Content-Type": "application/x-gk-json",
                        "X-APP-CODE": "y3",
                        "X-APP-DEVICE": "samsung SM-G955N", #TODO: maybe?
                        "X-APP-VERSION": app_version,
                        "X-APP-PLATFORM": "Android 5.1.1", #TODO: this too? though realistically who even cares about setting these variables. maybe they could be randomized to cover tracks...
                        "X-Unity-Version": "2017.4.20f2"
            }
        )
        self.get_app_version()
        self.start_session()

    def get_app_version(self):
        """Checks to see if the server requires a new version, updates the session header if necessary
        """
        response = self.api_request("GET", APIEndpoints.requirement_version)
        if response["requirement_version"]["need_update"]:
            self.session.headers.update({"X-APP-VERSION": response["requirement_version"]["version"]})
            self.required_update = True

    def start_session(self):
        """Starts a session using the provided ``UUID`` and assigns the ``gk_api_key`` given by the server.

        Though the server will happily continue using the default key
        if this is never called... it should be used anyways to look more legit.
        """
        request_body = str.encode(json.dumps({"uuid": self.uuid}))
        response = self.api_request("POST", APIEndpoints.sessions, request_body=request_body)
        self.session.cookies.update({"_session_id": response["session_id"]})
        self.api_crypter.setkey(key=response["gk_key"])
        self.logger.debug(f"[red]gk_api_key[/red] set to [red]{response['gk_key']}[/red]")

    def log_json(self, response: object, path: object):
        """Saves the json file, then logs it to the console if it's an api result.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        jstring = json.dumps(response, indent=2)
        path.write_text(jstring)
        if str(path).startswith("y3/api"): #yeah lets go ahead and *not* print a giant 1000+ item json object to the console
            self.logger.debug(jstring)

    def api_request(self, method: str, endpoint: Enum, *endpoint_args, request_body=None) -> object:
        """Generic request handler that encrypts the body if given one, and returns the decrypted response.
        """
        if request_body: #POST or PUT
            request_body = self.api_crypter.encrypt(input=request_body)
        response = self.session.request(method, str(endpoint).format(*endpoint_args), data=request_body)
        response.raise_for_status()
        response_decrypted = json.loads(self.api_crypter.decrypt(input=response.content).decode("utf-8"))
        self.log_json(response_decrypted, Path(f"y3/api{endpoint.value.format(*endpoint_args)}.json"))
        return response_decrypted

    @staticmethod
    def format_as_date(date: str) -> str:
        """Format date string as ``MM/DD/YYYY HH:mm:ss``.
        """
        return f"[{date[4:6]}/{date[6:8]}/{date[0:4]} {date[8:10]}:{date[10:12]}:{date[12:14]}]"
    
    @staticmethod
    def format_as_update(local_date: str, server_date: str) -> str:
        return f"v[{server_date[4:6]}-{server_date[6:8]}-{server_date[0:4]}]" #"v[{local_date[4:6]}-{local_date[6:8]}-{local_date[0:4]}]-[{server_date[4:6]}-{server_date[6:8]}-{server_date[0:4]}]"

    def get_vlist_updates(self, vtype: str, write=None) -> list:
        """Compares ``vlist`` versions for the given ``vtype`` , then logs the timestamp as a human readable string.

        If the ``write`` flag is set, the local version will be overwritten when an update is found.
        """
        server_vlist = self.api_request("GET", APIEndpoints.resource_versions, vtype)
        local_path = Path(f"y3/v_lists/{vtype}/{PathHelper.PLATFORM}/{vtype}.json")
        updated_manifests = []
        try:
            local_vlist = json.loads(local_path.read_text())
            for manifest in server_vlist["version"]:
                server_time = self.format_as_date(server_vlist["version"][manifest]["version"])
                local_time = self.format_as_date(local_vlist["version"][manifest]["version"])

                if server_time == local_time:
                    comparison_string = "========   No changes   ========"
                else:
                    if server_time > local_time:
                        comparison_string = "--> Version Increment Update -->"
                    else: 
                        comparison_string = "--> Version Decrement Update -->" #this probably wont ever happen

                    if manifest == "master_data":
                        self.resource_types |= ResourceTypes.MASTER_DATA
                    if manifest == "asset_bundle":
                        self.resource_types |= ResourceTypes.ASSET_BUNDLE
                    updated_manifests.append(
                        (
                            server_vlist["version"][manifest]["url"],
                            self.format_as_update(
                                local_vlist["version"][manifest]["version"],
                                server_vlist["version"][manifest]["version"]
                            )
                        )
                    )
                self.logger.info(f"{manifest:>12} | Local: {local_time} | {comparison_string} | Server: {server_time}")
        except FileNotFoundError:
            print("No local version found, getting all manifests.")
            for manifest in server_vlist["version"]:
                updated_manifests.append(
                    (server_vlist["version"][manifest]["url"], None)
                )
            pass
        if write:
            self.log_json(server_vlist, local_path) #write as local version list
        return updated_manifests

    @staticmethod
    def get_manifest(url: str) -> dict:
        """Gets and restructures a resource manifest because the raw one straight from the servers has a ton of redundant data.
        """
        raw_manifest = httpx.get(url).json()
        # restructure as a nested dictionary for easier checking
        fixed_manifest = {
            key["name"]: {
                "hash": key["hash"],
                "url": key["url"],
                "encrypt": key["encrypt"],
                "filesize": key.get("filesize")
                # "filesize": key["filesize"]
            }
            for key in raw_manifest["resources"]
        }
        return fixed_manifest

    @staticmethod
    def format_bytes(bint: int) -> str:
        """Quick and easy conversion from ``int`` to a readable filesize ``string``
        """
        _byte = float(bint)
        kilobyte = float(1024)
        megabyte = float(1048576)
        gigabyte = float(1073741824)

        if _byte < megabyte:
            return f"{(_byte/kilobyte):.2f} KB"
        elif _byte >= megabyte < gigabyte:
            return f"{(_byte/megabyte):.2f} MB"
        else:
            print("///FORESTIZATION WARNING/// why is the server downloading a 1gb+ file?!")
            return f"{(_byte/megabyte):.2f} MB"

    def resource_check(self, new_resource: dict, old_resource: dict, name: str) -> bool:
        """Compares one manifest resource to another, returns true if hashes are different. Writes changes to the changelog
        """
        if new_resource["hash"] == old_resource["hash"]:
            return False
        else:
            # :>56 justifies right based on the size of what i HOPE is the largest name, "battle/mat_parset_8_additivewithalphablendedforgrayscale"
            changed = f"{name:>56} | Filesize: {self.format_bytes(old_resource['filesize']):>10} | --> Resource modified --> | Filesize: {self.format_bytes(new_resource['filesize']):>10}"
            self.logger.info(changed)
            return True       

    def get_updates(self, *vlists, write=None) -> dict:
        """Takes a vlist, or multiple vlists like ``game`` or ``scenario_common`` and handles the entire update check and download process.
        
        Only problem is at the moment it doesnt actually check to see if files exist or not, it just assumes the state of the downloads folder and hopes for the best.
        """
        download_list = {} #actually a dictionary but whatever
        for vtype in vlists:
            updated_manifests = self.get_vlist_updates(vtype, write=True)
            if not updated_manifests:
                self.logger.info("Local matches server, no update found")
                continue
            for manifest, update_name in updated_manifests:
                server_manifest = self.get_manifest(manifest)
                #convert manifest_url into path object, e.g. "y3/v_list/game/android/master_data/..." or manifest/scenario/ay001_m001_a
                archive_path = Path("y3/v_lists/", *manifest.split("/")[4:])
                #semi-cursed path mutation to use the parent directory as a json filename. this is where the "current" version goes
                local_path = Path(f"{str(archive_path.parent)}.json")
                try:
                    temp_list = {}
                    local_manifest = json.loads(local_path.read_text())
                    for resource, values in server_manifest.items():
                        if resource not in local_manifest:
                            temp_list = {resource: values}
                        elif self.resource_check(values, local_manifest[resource], resource):
                            temp_list = {resource: values}
                        else:
                            continue
                        download_list = {**download_list, **temp_list}
                except FileNotFoundError:
                    self.logger.info(f"No local manifest found for {str(local_path)}. Marking all resources as new.")
                    download_list = {**download_list, **server_manifest}
                    pass
                if write:
                    #save a current copy and an archive copy
                    self.log_json(server_manifest, local_path)
                    self.log_json(server_manifest, archive_path)
                if update_name:
                    #TODO: this is extremely broken and needs reworking but it only affects filenames so...
                    self.update_str = update_name
                    self.log_json(download_list, Path(f"y3/v_lists/update_lists/{vtype}.{update_name}.json"))
        return download_list

    def get_scenario(self, *scenario_ids: str) -> dict:
        download_list = {}
        for scenario_id in scenario_ids:
            sleep(random.uniform(1.139, 3.653))
            server_vlist = self.api_request("GET", APIEndpoints.resource_versions, f"scenario/{scenario_id}")
            for manifest in server_vlist["version"]:
                resources = self.get_manifest(server_vlist["version"][manifest]["url"])
                download_list = {**download_list, **resources}
        return download_list

    def download_file(self, filename: str, url: str, decrypt=None, export_new=None):
        exports = Path("y3/exports")
        resources = Path("y3/resources")
        if filename.endswith(".compress"):
            file_path = resources.joinpath(PathHelper.PLATFORM, filename[:-9]) #remove fake file extension
            new_path = exports.joinpath(f"new_{filename[:-9]}")
            log_message = f"Downloading [red]master_database[/red]: {filename[:-9]}"
        
        elif filename.endswith((".acb", ".awb")):
            decrypt=False #the manifest LIES
            file_path = resources.joinpath(PathHelper.PLATFORM, filename)
            new_path = exports.joinpath(f"new_{filename}")
            log_message = f"Downloading [red]sound_archive[/red]: {filename}"
        
        elif filename.endswith(".db"):
            self.logger.info(f"Ignoring unencrypted database: {filename}")
            return

        else:
            file_path = resources.joinpath(PathHelper.PLATFORM, "assetbundle", filename)
            new_path = exports.joinpath("new_assetbundle", filename)
            log_message = f"Downloading [red]asset_bundle[/red]: {filename}"

        self.logger.info(log_message)
        data = httpx.get(url).content

        if decrypt:
            data = self.asset_crypter.decrypt(input=data)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        if export_new:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.write_bytes(data)

    def decrypt(self, input_data):
        return self.asset_crypter.decrypt(input=input_data)
