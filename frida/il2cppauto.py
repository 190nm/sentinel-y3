
import json
from pathlib import Path
from rich import print
from collections import namedtuple
from typing import Set

ScriptData = namedtuple("ScriptData", [
        "methods",
        "metadata",
        "metadatamethod",
        "strings"
    ])

def from_script(script_json: Path) -> ScriptData:
    rawdict = json.loads(script_json.read_text())

    scriptmethods = {key["Name"]: key["Signature"] for key in rawdict["ScriptMethod"]}
    scriptmetadata = {key["Name"]: key["Signature"] for key in rawdict["ScriptMetadata"]}
    scriptmetadatamethod = {key["Name"] for key in rawdict["ScriptMetadataMethod"]}
    scriptstrings = {key["Value"] for key in rawdict["ScriptString"]}

    return ScriptData(scriptmethods, scriptmetadata, scriptmetadatamethod, scriptstrings)

def diff_scripts():
    print("processing newscript...")
    newscript = from_script(Path("frida/script_new.json"))
    print("processing oldscript...")
    oldscript = from_script(Path("frida/script_old.json"))


    # print("[blue]Methods[blue]:")
    # print({v for k, v in newscript.methods.items() if k not in oldscript.methods})
    # print("[blue]Metadata[blue]:")
    # print({v for k, v in newscript.metadata.items() if k not in oldscript.metadata})
    # print("[blue]MetadataMethod[/blue]:")
    # print({item for item in newscript.metadatamethod if item not in oldscript.metadatamethod})
    # print("[blue]Strings[/blue]:")
    # print({item for item in newscript.strings if item not in oldscript.strings})

    print("[blue]Methods[blue]:")
    print(sorted({v for k, v in newscript.methods.items() if k not in oldscript.methods}))
    print("[blue]Metadata[blue]:")
    print(sorted({v for k, v in newscript.metadata.items() if k not in oldscript.metadata}))
    print("[blue]MetadataMethod[/blue]:")
    print(sorted({item for item in newscript.metadatamethod if item not in oldscript.metadatamethod}))
    print("[blue]Strings[/blue]:")
    print(sorted({item for item in newscript.strings if item not in oldscript.strings}))

def export_and_format_il2cpp(script_json: Path):
    rawdict = json.loads(script_json.read_text())
    scriptmethods = {
        key["Signature"]: {
            "Name": key["Name"],
            "Address": hex(key["Address"])
        } for key in rawdict["ScriptMethod"]
    }
    scriptmetadata = {
        key["Signature"]: {
            "Name": key["Name"],
            "Address": hex(key["Address"])
        } for key in rawdict["ScriptMetadata"]
    }
    scriptmetadatamethod = {
        key["Name"]: {
            "Address": hex(key["Address"]),
            "MethodAddress": hex(key["MethodAddress"])
        } for key in rawdict["ScriptMetadataMethod"]
    }
    scriptstrings = {key["Value"]: key["Address"] for key in rawdict["ScriptString"]}
    path = Path("frida/il2cpp")
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("methods.json").write_text(json.dumps(scriptmethods, indent=2))
    path.joinpath("metadata.json").write_text(json.dumps(scriptmetadata, indent=2))
    path.joinpath("metadatamethod.json").write_text(json.dumps(scriptmetadatamethod, indent=2))
    path.joinpath("strings.json").write_text(json.dumps(scriptstrings, indent=2, ensure_ascii=False))

def export_frida_payload(script_json: Path, func_names: Set[str]):
    """Accepts a script file, and a set of desired function names to export. Generates a frida payload with correct offsets based on the template in the folder.
    """
    rawdict = json.loads(script_json.read_text())
    frida_magic = {key["Signature"]: key["Address"] for key in rawdict["ScriptMethod"] if key["Name"] in func_names}
    template_magic = f"var magic = {json.dumps(frida_magic, indent=2)}"
    template = Path("frida/frida-payload.jstemplate").read_text()
    Path("frida/frida-payload.js").write_text(template.replace("//=== magic placeholder ===//", template_magic))
    print(template_magic)


frida_func_names = {
    "System.IO.File$$Exists",
    "System.IO.File$$ReadAllText",
    "UnityEngine.Application$$get_persistentDataPath",
    "Y3.Data.SqlDataStore$$.ctor",
    "SQLite4Unity3d.SQLiteConnection$$.ctor",
    "SQLite4Unity3d.SQLiteConnection$$Execute",
    "Y3.ScenarioPrivateResourceManager$$GetScenarioText",
    "biscuit.Scenario.UI.WindowTextView$$SetText",
    "Y3.Utils.IOUtil$$NativeLog",
    "UnityEngine.Debug$$Log",
    "UnityEngine.Debug$$LogError",
    "Y3.Data.MasterDataStore$$MakeCacheFileName",
}
diff_scripts()
# frida -U -f jp.co.altplus.yuyuyui -l Downloads/fridascript.js --no-paus
# export_frida_payload(Path("tests/script_new.json"), frida_func_names)
# export_and_format_il2cpp(Path("tests/script_new.json"))
