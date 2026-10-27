#!/usr/bin/env python3
"""One-off data baker. The generator itself needs only the Python standard library.

Writes tools/data/glyphs.json (Inter outlines + kerning, for text drawn as paths) and
tools/data/icons.json (brand icon paths).

  pip install fonttools uharfbuzz
  npm i simple-icons devicon            # in any scratch folder
  python3 tools/bake_data.py --fonts /usr/share/fonts/opentype/inter --npm <scratch>/node_modules

Inter is SIL OFL 1.1. simple-icons is CC0. devicon is MIT. Brand marks belong to their owners.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--fonts", required=True)
ap.add_argument("--npm", required=True)
a = ap.parse_args()
DATA = Path(__file__).resolve().parent / "data"
DATA.mkdir(exist_ok=True)


def n(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------------ glyphs
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import uharfbuzz as hb


class Pen(BasePen):
    def __init__(self, gs, k):
        super().__init__(gs)
        self.k, self.out = k, []

    def pt(self, p):
        return f"{n(p[0] * self.k)} {n(-p[1] * self.k)}"

    def _moveTo(self, p): self.out.append("M" + self.pt(p))
    def _lineTo(self, p): self.out.append("L" + self.pt(p))
    def _curveToOne(self, a, b, c): self.out.append("C" + " ".join(map(self.pt, (a, b, c))))
    def _qCurveToOne(self, a, b):
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2 / 3 * (a[0] - p0[0]), p0[1] + 2 / 3 * (a[1] - p0[1]))
        c2 = (b[0] + 2 / 3 * (a[0] - b[0]), b[1] + 2 / 3 * (a[1] - b[1]))
        self.out.append("C" + " ".join(map(self.pt, (c1, c2, b))))
    def _closePath(self): self.out.append("Z")


chars = [chr(c) for c in range(32, 127)] + ["’", "·"]
glyphs = {}
for weight, fname in ((600, "Inter-SemiBold.otf"), (800, "Inter-ExtraBold.otf")):
    path = Path(a.fonts) / fname
    font = TTFont(str(path))
    upm = font["head"].unitsPerEm
    k = 1000 / upm
    cmap, gs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
    d, adv = {}, {}
    for ch in chars:
        gn = cmap[ord(ch)]
        pen = Pen(gs, k)
        gs[gn].draw(pen)
        d[ch] = "".join(pen.out)
        adv[ch] = hmtx[gn][0] * k
    blob = hb.Blob.from_file_path(str(path))
    hbfont = hb.Font(hb.Face(blob))
    kern = {}
    for x in chars:
        for y in chars:
            buf = hb.Buffer()
            buf.add_str(x + y)
            buf.guess_segment_properties()
            hb.shape(hbfont, buf, {"kern": True, "liga": False, "calt": False})
            delta = buf.glyph_positions[0].x_advance * k - adv[x]
            if abs(delta) > 0.5:
                kern[x + y] = round(delta, 1)
    glyphs[str(weight)] = {"d": d, "adv": {c: round(v, 1) for c, v in adv.items()}, "kern": kern}
    print("glyphs", weight, len(d), "kern pairs", len(kern))
(DATA / "glyphs.json").write_text(json.dumps(glyphs, separators=(",", ":")))

# ------------------------------------------------------------------ icons
node = f"""
const si=require('{a.npm}/simple-icons');
const want={{javascript:'siJavascript',python:'siPython',kotlin:'siKotlin',cpp:'siCplusplus',react:'siReact',
threejs:'siThreedotjs',angular:'siAngular',html:'siHtml5',tailwind:'siTailwindcss',gcp:'siGooglecloud',
cloudflare:'siCloudflare',docker:'siDocker',linux:'siLinux',postgres:'siPostgresql',mongodb:'siMongodb',
redis:'siRedis',supabase:'siSupabase',firebase:'siFirebase'}};
const out={{}};
for(const [k,v] of Object.entries(want)){{const i=si[v];out[k]={{vb:24,title:i.title,paths:[{{d:i.path,fill:'#'+i.hex}}]}}}}
console.log(JSON.stringify(out));
"""
icons = json.loads(subprocess.run(["node", "-e", node], capture_output=True, text=True, check=True).stdout)
dev = Path(a.npm) / "devicon" / "icons"
for key, title, rel in (
    ("csharp", "C#", "csharp/csharp-original.svg"),
    ("java", "Java", "java/java-original.svg"),
    ("css", "CSS", "css3/css3-original.svg"),
    ("aws", "AWS", "amazonwebservices/amazonwebservices-original.svg"),
):
    svg = (dev / rel).read_text()
    paths = []
    for m in re.finditer(r"<path\b([^>]*)>", svg):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        paths.append({"d": attrs["d"], "fill": attrs.get("fill", "")})
    others = re.findall(r"<(circle|rect|polygon|ellipse|g)\b", svg)
    assert not others, (key, others)
    icons[key] = {"vb": 128, "title": title, "paths": paths}
(DATA / "icons.json").write_text(json.dumps(icons, separators=(",", ":")))
print("icons", len(icons))
