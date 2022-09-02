import json
import struct
from collections import namedtuple
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from rich import print

uint32_t = struct.Struct("<I")


def Read(struct_type, buffer, offset):
    return struct_type.unpack_from(buffer, offset)[0]


def Read_Str(buffer, offset):
    # read length
    length = Read(uint32_t, buffer, offset)
    # "seek" to the string
    offset += 0x4
    return buffer[offset : (offset + length)].decode()


def Parse_opy():
    """Test"""

    opypath = Path("yuyuyui_UserData.opy")
    if opypath.exists():
        data = Path("yuyuyui_UserData.opy").read_bytes()
    else:
        raise FileNotFoundError(
            "A UserData file is required. It can be found at android/data/jp.co.altplus.yuyuyui/files/yuyuyui_UserData.opy"
        )
    # TODO must not be pushed to public git branch
    config = {
        "app_version": "2.14.0",
        "auth_username": "yuyuyudev",
        "auth_password": "4c9apk76ewxrtbw5",
        "gk_api_key": "db9a0d951de48825",
        "gk_asset_iv": "2929beef0a0c0170ed0e0affecbddccb",
        "aes_opy_key": "cve4hbq9sjvawhvdr9kvhpfm5qv393ga",
        "aes_opy_iv": "1234567890123456",
        "userCode": "",
        "uuid": "",
    }
    cipher = AES.new(
        key=config["aes_opy_key"].encode(),
        mode=AES.MODE_CBC,
        iv=config["aes_opy_iv"].encode(),
    )
    # see https://google.github.io/flatbuffers/flatbuffers_internals.html
    Table = namedtuple(
        "Table",
        [
            "root_table_offset",
            "magic",
            "table_size",
            "object_size",
            "userCode_root_table_offset",
            "uuid_root_table_offset",
            "vtable_offset",
            "userCode_offset",
            "uuid_offset",
        ],
    )
    dec_bytes = unpad(padded_data=cipher.decrypt(data), block_size=128, style="pkcs7")
    fb_header = struct.Struct("<IIHHHHiII")
    # read header
    fb = Table._make(fb_header.unpack_from(dec_bytes))
    # check for "USDT" file identifier magic
    if fb.magic != 0x54445355:
        raise EOFError("Invalid .opy header")
    # sorta messy offset fixups to read strings from the buffer
    userCode = Read_Str(dec_bytes, fb.root_table_offset + 0x4 + fb.userCode_offset)
    uuid = Read_Str(dec_bytes, fb.root_table_offset + 0x8 + fb.uuid_offset)
    print("userCode:", userCode)
    print("uuid:", uuid)
    print("writing config")
    configpath = Path("config.json")
    config["userCode"] = userCode
    config["uuid"] = uuid
    configpath.write_text(json.dumps(config, indent=2))
