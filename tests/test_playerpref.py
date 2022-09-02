from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pathlib import Path
from rich import print
from collections import namedtuple

import struct
import json

uint8 = struct.Struct("<B")
uint16 = struct.Struct("<H")
uint32 = struct.Struct("<I")
uint64 = struct.Struct("<Q")

int8 = struct.Struct("<b")
int16 = struct.Struct("<h")
int32 = struct.Struct("<i")
int64 = struct.Struct("<q")

fb_header = struct.Struct("<IIHHHHiII")

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
    ]
)

def Read(struct_type, buffer, offset):
    return struct_type.unpack_from(buffer, offset)[0]

def Read_Str(buffer, offset):
    # read length
    length = Read(uint32, buffer, offset)
    # "seek" to the string
    offset += 0x4
    return buffer[offset : (offset + length)].decode()

#TODO must not be pushed to public git branch
configpath = Path("tests/config.json")
if configpath.exists():
    config = json.loads(configpath.read_text())
else:
    print("writing config")
    config = {
        "auth_id": "yuyuyudev",
        "auth_pass": "4c9apk76ewxrtbw5",
        "api_key": "db9a0d951de48825",
        "gk_asset_key": "8d49d9db4439e344",
        "aes_opy_key": "cve4hbq9sjvawhvdr9kvhpfm5qv393ga",
        "aes_opy_iv": "1234567890123456",
        "userCode": "",
        "uuid": "",
        "version": "2.11.0",

    }
    configpath.write_text(json.dumps(config, indent=2))

data = Path("tests/yuyuyui_UserData.opy").read_bytes()

cipher = AES.new(
    key=config["aes_opy_key"].encode(),
    mode=AES.MODE_CBC,
    iv=config["aes_opy_iv"].encode(),
)
dec_bytes = unpad(padded_data=cipher.decrypt(data), block_size=128, style="pkcs7")

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

config["userCode"] = userCode
config["uuid"] = uuid
configpath.write_text(json.dumps(config, indent=2))
