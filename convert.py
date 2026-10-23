"""Convierte stories/*.png a jpg/*.jpg (Instagram solo acepta JPEG)."""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).parent
SRC, DST = ROOT / "stories", ROOT / "jpg"
DST.mkdir(exist_ok=True)

for png in sorted(SRC.glob("*.png")):
    jpg = DST / (png.stem + ".jpg")
    if jpg.exists() and jpg.stat().st_mtime >= png.stat().st_mtime:
        continue
    img = Image.open(png)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.save(jpg, "JPEG", quality=92, optimize=True)
    print(f"{png.name} → {jpg.name}")
