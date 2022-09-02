
import json
import re
import sqlite3
import sys
from enum import Enum, Flag, auto
from pathlib import Path

import httpx
from rich import print
import Y3gk

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
    def __init__(self, app_version: str, gk_key: str, uuid: str, no_connect=None):
        """Set ``verbose_logging`` to show api calls while running.
        """
        self.uuid = uuid
        self.gk_key = gk_key
        self.required_update = None
        self.update_str = None
        self.resource_types = ResourceTypes.NULL
        self.current_vlist_version = None
        self.server_vlist_version = None
        self.api_crypter = Y3gk.Igarashi(key=self.gk_key)
        if not no_connect:
            self.session = httpx.Client(
                auth=("yuyuyudev", "4c9apk76ewxrtbw5"),
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
        """Starts a session using the provided ``UUID`` and assigns the ``gk_key`` given by the server.

        Though the server will happily continue using the default key
        if this is never called... it should be used anyways to look more legit.
        """
        request_body = str.encode(json.dumps({"uuid": self.uuid}))
        response = self.api_request("POST", APIEndpoints.sessions, request_body=request_body)
        self.session.cookies.update({"_session_id": response["session_id"]})
        self.gk_key = response["gk_key"]
        self.api_crypter.setkey(key=response["gk_key"])
        print(f"[red]gk_key[/red] set to [red]{self.gk_key}[/red]")

    def api_request(self, method: str, endpoint: Enum, *endpoint_args, request_body=None) -> object:
        """Generic request handler that encrypts the body if given one, and returns the decrypted response.
        """
        if request_body: #POST or PUT
            request_body = self.api_crypter.encrypt(input=request_body)
        response = self.session.request(method, str(endpoint).format(*endpoint_args), data=request_body)
        response.raise_for_status()
        testbyte = self.api_crypter.decrypt(input=response.content)
        teststr = testbyte.decode("utf-8")
        response_decrypted = json.loads(teststr)
        self.log_json(response_decrypted, Path(f"y3/api{endpoint.value.format(*endpoint_args)}.json"))
        return response_decrypted

    def log_json(self, response: object, path: object):
        """Saves the json file, then logs it to the console if it's an api result.
        """
        jstring = json.dumps(response, indent=2)
        print(jstring)

# client = Y3APISession(
#     "2.14.0",
#     "db9a0d951de48825",
#     "36e81f0cd1094750bcf5281730c4d515a2b2ed23d37a445c9be0aa29f1f72ffa",
#     no_connect=False
#     )
# download_list = client.api_request("GET", APIEndpoints.resource_versions, "game")
# print(download_list)

# test = Y3gk.Igarashi(key="deadbeef11223344")
# test = Y3gk.Igarashi(key="db9a0d951de48825")
# sample_request = str.encode('{"uuid":"36e81f0cd1094750bcf5281730c4d515a2b2ed23d37a445c9be0aa29f1f72ffa"}')
# encrypted_request = test.encrypt(input=sample_request)
# decrypted_request = test.decrypt(input=encrypted_request)
# if sample_request == decrypted_request:
#     print("yay! theyre the same!")


# sample_response = Path("testresponse.bin").read_bytes()
# test.setkey(key="33e785383ba758c5")
# decrypted_response = test.decrypt(input=sample_response)
# print(type(decrypted_response))
# response = json.loads(decrypted_response)
# print(json.dumps(response, indent=2))
# print("done!")
# # test_iv = bytes.fromhex("2929BEEF0A0C0170ED0E0AFFECBDDCCB")
test_iv = bytes.fromhex("2929beef0a0c0170ed0e0affecbddccb")
test2 = Y3gk.Takeshi(iv=test_iv)
sample_asset = Path("image_301771.asset").read_bytes()
decrypted_asset = test2.decrypt(input=sample_asset)
Path("image_301771_decrypted.asset").write_bytes(decrypted_asset)
print("done!")