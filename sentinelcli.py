#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
from pathlib import Path
from rich import print

import sys
import json
from sentinel.classes.Y3APISession import Y3APISession, APIEndpoints, ResourceTypes
from sentinel.classes.Y3AssetBundleReader import Y3AssetBundleReader
from sentinel.classes.Y3MasterDatabase import Y3MasterDatabase, Adventure_Books
from sentinel.helpers import PathHelper, LogHelper

# sys.tracebacklimit = 0

configpath = Path("config.json")
if not configpath.exists():
    from sentinel.helpers import ConfigHelper
    ConfigHelper.Parse_opy()
config = json.loads(configpath.read_text())

testuuid = "d60fb1cd4fb042798392443ccdafbd336a05680990c2467eacfb63418b348bfd"

client = Y3APISession(
    config["app_version"],
    config["uuid"],
    # testuuid,
    config["auth_username"],
    config["auth_password"],
    config["gk_api_key"],
    config["gk_asset_iv"],
    )

if client.required_update:# Request version, store to config
    config["app_version"] = client.session.headers["X-APP-VERSION"]
    configpath.write_text(json.dumps(config, indent=2))

# sample_asset = Path("image_301771.asset").read_bytes()
# Path("image_301771_decrypted.asset").write_bytes(client.decrypt(sample_asset))

# db_reader = Y3MasterDatabase(platform=PathHelper.Platform.android, previous_version="test", is_english=False)
# test = db_reader.connect_mdb(Adventure_Books)
# test.row_factory = lambda cursor, row: row[0]
# scenario_ids = test.execute("SELECT file_id FROM adventure_books").fetchall()
# test.connection.close()
# print(scenario_ids)
# ab_reader = Y3AssetBundleReader()
# ab_reader.export_assets(to_root=False, optimize=False)  

download_list = client.get_updates("game", "scenario_common", write=False)
PathHelper.clear_new_resources()
PathHelper.clear_extracted()

if ResourceTypes.MASTER_DATA in client.resource_types:
    #copy mdbs to folder
    old_path = Path("y3/exports/old_master_data/", client.update_str)
    old_path.mkdir(parents=True, exist_ok=True)
    for child in Path(PathHelper.CURRENT_PATH).iterdir():
        if child.is_file():
            file = child.read_bytes()
            copy = old_path.joinpath(child.name)
            copy.write_bytes(file)
            
# reduce console spam
LogHelper.set_filter(LogHelper.HTTP_DISALLOWED)
# download_list = client.get_scenario(*test)
for key, values in download_list.items():
    client.download_file(
        filename=key,
        url=values["url"],
        decrypt=values["encrypt"],
        export_new=True,
    )
LogHelper.set_filter(LogHelper.HTTP_ALLOWED)

# if ResourceTypes.ASSET_BUNDLE in client.resource_types: #TODO: maybe use enum flags or something
#     ab_reader = Y3AssetBundleReader()
#     ab_reader.export_assets(to_root=False, optimize=False)        

if ResourceTypes.MASTER_DATA in client.resource_types:
    db_reader = Y3MasterDatabase(platform=PathHelper.Platform.android, previous_version=client.update_str, is_english=False)
    db_reader.make_changelog(client.update_str)
