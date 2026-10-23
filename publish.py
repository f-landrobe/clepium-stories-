"""Publica la tanda de stories del día en la página de Facebook y en Instagram.

- Las tandas salen de jpg/storyNN-M.jpg (NN = tanda, M = orden dentro de la tanda).
- Recorre las tandas en loop: después de la última vuelve a la primera.
- state.json guarda la última tanda publicada y la fecha, para no repetir en el mismo día.
"""
import datetime
import json
import os
import pathlib
import re
import sys
import time

import requests

GRAPH = "https://graph.facebook.com/v23.0"
TOKEN = os.environ["META_TOKEN"]
PAGE_ID = os.environ["FB_PAGE_ID"]
IG_ID = os.environ["IG_USER_ID"]
REPO = os.environ["GITHUB_REPOSITORY"]          # lo completa GitHub Actions
BRANCH = os.environ.get("BRANCH", "main")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
FORCE_TANDA = os.environ.get("FORCE_TANDA", "").strip()
TARGETS = [t.strip() for t in os.environ.get("TARGETS", "fb,ig").split(",") if t.strip()]

ROOT = pathlib.Path(__file__).parent
JPG_DIR = ROOT / "jpg"
STATE_FILE = ROOT / "state.json"
PATTERN = re.compile(r"story(\d+)-(\d+)\.jpg$", re.IGNORECASE)
TZ_BA = datetime.timezone(datetime.timedelta(hours=-3))


def load_tandas():
    tandas = {}
    for f in JPG_DIR.glob("*.jpg"):
        m = PATTERN.match(f.name)
        if m:
            tandas.setdefault(int(m[1]), []).append((int(m[2]), f))
    return {k: [f for _, f in sorted(v)] for k, v in sorted(tandas.items())}


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tanda": None, "last_date": None, "history": []}


def next_tanda(keys, last):
    if last is None:
        return keys[0]
    later = [k for k in keys if k > last]
    return later[0] if later else keys[0]


def api(method, path, **params):
    params["access_token"] = TOKEN
    r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"{path}: {body['error'].get('message')}")
    return body


def public_url(f):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/jpg/{f.name}"


def publish_fb(f):
    photo = api("POST", f"{PAGE_ID}/photos", url=public_url(f), published="false")
    return api("POST", f"{PAGE_ID}/photo_stories", photo_id=photo["id"])


def publish_ig(f):
    container = api("POST", f"{IG_ID}/media", image_url=public_url(f), media_type="STORIES")
    cid = container["id"]
    for _ in range(24):  # hasta 2 minutos
        status = api("GET", cid, fields="status_code").get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"contenedor IG {cid} en estado {status}")
        time.sleep(5)
    else:
        raise RuntimeError(f"contenedor IG {cid} no terminó de procesar")
    return api("POST", f"{IG_ID}/media_publish", creation_id=cid)


def main():
    tandas = load_tandas()
    if not tandas:
        sys.exit("No hay imágenes en jpg/. ¿Corrió la conversión?")

    state = load_state()
    today = datetime.datetime.now(TZ_BA).date().isoformat()

    if FORCE_TANDA:
        tanda = int(FORCE_TANDA)
        if tanda not in tandas:
            sys.exit(f"La tanda {tanda} no existe. Disponibles: {list(tandas)}")
    else:
        if state.get("last_date") == today:
            print(f"Ya se publicó la tanda {state['last_tanda']} hoy ({today}). Nada que hacer.")
            return
        tanda = next_tanda(list(tandas), state.get("last_tanda"))

    files = tandas[tanda]
    print(f"Tanda {tanda} ({len(files)} imágenes) → {', '.join(TARGETS)}{' [SIMULACIÓN]' if DRY_RUN else ''}")

    ok, errors = 0, []
    for f in files:
        for target in TARGETS:
            if DRY_RUN:
                print(f"  [{target}] {f.name} → {public_url(f)}")
                continue
            try:
                result = publish_fb(f) if target == "fb" else publish_ig(f)
                print(f"  [{target}] {f.name} OK {result}")
                ok += 1
            except Exception as e:  # sigue con el resto aunque falle una
                print(f"  [{target}] {f.name} ERROR {e}")
                errors.append(f"{target} {f.name}: {e}")
            time.sleep(3)

    if not DRY_RUN and ok:
        state["last_tanda"] = tanda
        state["last_date"] = today
        state.setdefault("history", []).append({"date": today, "tanda": tanda, "ok": ok, "errors": len(errors)})
        state["history"] = state["history"][-60:]
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    if errors:
        sys.exit("Hubo errores:\n" + "\n".join(errors))


if __name__ == "__main__":
    main()
