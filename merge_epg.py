import os, gzip, requests
import xml.etree.ElementTree as ET

URLS = [u.strip() for u in os.environ["EPG_URLS"].splitlines() if u.strip()]

def indir(url):
    r = requests.get(url, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    b = r.content
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b

kanallar, prog = {}, {}
for i, url in enumerate(URLS, 1):
    try:
        tv = ET.fromstring(indir(url))
    except Exception as e:
        print(f"::warning::EPG {i} alınamadı: {e}")
        continue
    k = p = 0
    for el in tv:
        if el.tag == "channel":
            cid = el.get("id")
            if cid and cid not in kanallar:
                kanallar[cid] = el; k += 1
        elif el.tag == "programme":
            key = (el.get("channel"), el.get("start"))
            if key not in prog:
                prog[key] = el; p += 1
    print(f"EPG {i}: +{k} kanal, +{p} program")

if not prog:
    raise SystemExit("Hiç program yok, iptal")

kok = ET.Element("tv", {"generator-info-name": "umitmod-epg"})
kok.extend(kanallar.values())
kok.extend(sorted(prog.values(), key=lambda e: (e.get("channel") or "", e.get("start") or "")))
xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(kok, encoding="utf-8")
os.makedirs("out", exist_ok=True)
open("out/epg.xml", "wb").write(xml)
with gzip.open("out/epg.xml.gz", "wb", 9) as f:
    f.write(xml)
print(f"Toplam: {len(kanallar)} kanal, {len(prog)} program, {len(xml)//1024} KB")
