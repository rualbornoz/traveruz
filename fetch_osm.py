#!/usr/bin/env python3
"""Descarga de OpenStreetMap los servicios (baños, bebederos, parques, puntos de ayuda)
de cada ciudad y los guarda en osm/<ciudad>.json, junto a index.html.
Uso:  python3 fetch_osm.py            (todas las ciudades)
      python3 fetch_osm.py paris tokyo (solo algunas)
Requiere internet. Pone una pausa entre ciudades para respetar la API Overpass."""
import json, sys, time, os, urllib.request, urllib.parse

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps.js")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osm")
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]

txt = open(SRC, encoding="utf-8").read().strip()
MAPS = json.loads(txt[len("var MAPS = "):].rstrip(";"))
only = set(sys.argv[1:])
os.makedirs(OUT, exist_ok=True)

def bbox(m):
    pts = [(q[0], q[1]) for q in m["sl"]] + [(q[1], q[2]) for q in m["pl"]]
    pad = 0.012
    la = [p[0] for p in pts]; lo = [p[1] for p in pts]
    return "%.5f,%.5f,%.5f,%.5f" % (min(la) - pad, min(lo) - pad, max(la) + pad, max(lo) + pad)

def query(m):
    b = bbox(m)
    return ('[out:json][timeout:60];('
            'nwr["amenity"="toilets"](%s);nwr["amenity"="drinking_water"](%s);'
            'nwr["leisure"="park"]["name"](%s);nwr["amenity"~"^(police|hospital)$"](%s);'
            'nwr["tourism"="information"]["information"="office"](%s);nwr["emergency"="phone"](%s);'
            ');out center 700;') % ((b,) * 6)

for m in MAPS:
    if only and m["k"] not in only:
        continue
    data = urllib.parse.urlencode({"data": query(m)}).encode()
    for url in ENDPOINTS:
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "traveruz-prefetch/1.0"})
            res = json.load(urllib.request.urlopen(req, timeout=90))
            json.dump({"elements": res.get("elements", [])}, open(os.path.join(OUT, m["k"] + ".json"), "w"), ensure_ascii=False)
            print("OK  %-16s %d elementos" % (m["k"], len(res.get("elements", []))))
            break
        except Exception as e:
            print("ERR %-16s %s (%s)" % (m["k"], url, e))
    time.sleep(6)
