from collections import Counter
from pathlib import Path

from UnityPy import AssetsManager

from sentinel.helpers import LogHelper, PathHelper

class Y3AssetBundleReader:
    
    def __init__(self):
        self.logger = LogHelper.new_logger("sentinel.[green]y3assetbundlereader[/green]")
        self.am = AssetsManager("y3/exports/new_assetbundle")

    def export_assets(self, to_root=None, optimize=False):
        for asset in self.am.assets.values():
            extracted_path = Path("y3/exports/extracted")
            occurence_count = Counter(str(Path(asset_path).parent) for asset_path in asset.container.keys())
            asset_root = Path(*occurence_count.most_common(1)[0][0].split('/')[3:]) #removes 'assets/_yuyuyuassetbundles/resources'
            if not to_root:
                extracted_path = extracted_path.joinpath(asset_root)
            extracted_path.mkdir(parents=True, exist_ok=True)
            for obj in asset.objects.values():
                data = obj.read()
                if obj.type == "Texture2D":
                    filepath = extracted_path.joinpath(f"{data.name}.png")
                    # print(filepath)
                    data.image.quantize(method=2) #TODO method=3 (libimagequant) seems like it could be more efficient but PIL needs to be manually compiled with it enabled
                    #with my thorough N-of-1 study (lol), optimizing with method=2 seems to save literally 0.2399% on filesize while adding <$REALLY_BIG_NUMBER> times the processing time; not worth
                    data.image.save(fp=filepath, optimize=optimize)
                    self.logger.info(f"Exported: {asset_root}/[blue]{data.name}.png[/blue]")
                elif obj.type == "TextAsset":
                    filepath = extracted_path.joinpath(f"{data.name}.txt")
                    filepath.write_bytes(data.script)
                    self.logger.info(f"Exported: {asset_root}/[blue]{data.name}.txt[/blue]")