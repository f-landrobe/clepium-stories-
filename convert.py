"""Mantiene jpg/ como espejo de stories/: convierte los PNG nuevos a JPG (Instagram solo acepta JPEG)
y borra los JPG cuyo PNG ya no está, así una tanda quitada de stories/ deja de publicarse."""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).parent
SRC, DST = ROOT / "stories", ROOT / "jpg"
DST.mkdir(exist_ok=True)

pngs = {p.stem: p for p in SRC.glob("*.png")}

for jpg in DST.glob("*.jpg"):
    if jpg.stem not in pngs:
        jpg.unlink()
        print(f"{jpg.name} borrado (ya no está en stories/)")

for stem, png in sorted(pngs.items()):
    jpg = DST / (stem + ".jpg")
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
