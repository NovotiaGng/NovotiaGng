#!/usr/bin/env python3
"""Generates the README pictures: theme-adaptive SVGs (transparent ground, -dark / -light).

  python3 tools/gen_assets.py

Colours come from .design/tokens. Display type is drawn as outlines (tools/data/glyphs.json) so it
looks identical on every machine. Brand icons are embedded from tools/data/icons.json, so nothing
depends on an outside site. Standard library only.
"""
import json, math, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "brand"
TOK = ROOT / ".design" / "tokens"
OUT.mkdir(parents=True, exist_ok=True)

P = json.loads((TOK / "primitive.tokens.json").read_text())
S = json.loads((TOK / "semantic.tokens.json").read_text())
ICONS = json.loads((HERE / "data" / "icons.json").read_text())
GLY = json.loads((HERE / "data" / "glyphs.json").read_text())


# ------------------------------------------------------------------ tokens
def lookup(path):
    d = P
    for k in path.split("."):
        d = d[k]
    return d["$value"]


def resolve(v):
    m = re.fullmatch(r"\{(.+)\}", v)
    return lookup(m.group(1)) if m else v


def theme(mode):
    return {k: resolve(v["$value"]) for k, v in S[mode].items()}


FONT = lookup("font.sans")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


# ------------------------------------------------------------------ helpers
def n(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def norm(h):
    h = h.strip().lower()
    return "#" + "".join(c * 2 for c in h[1:]) if re.fullmatch(r"#[0-9a-f]{3}", h) else h


def lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def legible(c, bg, target=3.0):
    ext = "#ffffff" if lum(bg) < 0.5 else "#000000"
    t = 0.0
    while ratio(c, bg) < target and t < 1:
        t += 0.05
        c2 = mix(c, ext, t)
        if ratio(c2, bg) >= target:
            return c2
    return c if ratio(c, bg) >= target else mix(c, ext, 1)


_TOK = re.compile(r"[MLCZ]|-?\d+(?:\.\d+)?")


def xf(d, k, ox, oy):
    out, buf = [], []
    for tok in _TOK.findall(d):
        if tok in "MLCZ":
            out.append(tok)
        else:
            buf.append(float(tok))
            if len(buf) == 2:
                out.append(f"{n(buf[0] * k + ox)} {n(buf[1] * k + oy)}")
                buf = []
    return " ".join(out)


def layout(s, weight, size, tr=0.0):
    G = GLY[str(weight)]
    k = size / 1000
    x, items = 0.0, []
    for i, ch in enumerate(s):
        if ch not in G["d"]:
            ch = "?"
        items.append((ch, x, G["d"][ch]))
        nxt = s[i + 1] if i + 1 < len(s) else None
        x += (G["adv"][ch] + (G["kern"].get(ch + nxt, 0) if nxt else 0)) * k + tr * size
    return items, x - tr * size


def ptext(s, weight, size, x, y, fill, tr=0.0, anchor="start", extra=""):
    items, w = layout(s, weight, size, tr)
    if anchor == "middle":
        x -= w / 2
    k = size / 1000
    d = " ".join(xf(g, k, x + ix, y) for _, ix, g in items if g)
    return f'<path d="{d}" fill="{fill}" {extra}/>', w


def width_of(s, weight, size, tr=0.0):
    return layout(s, weight, size, tr)[1]


def gear_d(N, rp, m, phase=0.0, hole=0.3):
    rt, rr, p = rp + 0.75 * m, rp - 0.95 * m, 2 * math.pi / N
    pt = lambda r, a: (r * math.cos(a), r * math.sin(a))
    d = ""
    for i in range(N):
        a = math.radians(phase) + i * p
        a1, a2, a3, a4 = a - 0.30 * p, a - 0.15 * p, a + 0.15 * p, a + 0.30 * p
        x, y = pt(rr, a1)
        d += ("M" if i == 0 else "L") + f"{n(x)} {n(y)}"
        for r, ang in ((rt, a2), (rt, a3), (rr, a4)):
            x, y = pt(r, ang)
            d += f"L{n(x)} {n(y)}"
        nx, ny = pt(rr, a + p - 0.30 * p)
        d += f"A{n(rr)} {n(rr)} 0 0 1 {n(nx)} {n(ny)}"
    d += "Z"
    h = rp * hole
    d += f"M{n(h)} 0A{n(h)} {n(h)} 0 1 0 {n(-h)} 0A{n(h)} {n(h)} 0 1 0 {n(h)} 0Z"
    return d, rt


def gear(N, rp, m, fill, phase=0.0, T=24.0, rev=False, x=0.0, y=0.0):
    d, rt = gear_d(N, rp, m, phase)
    cls = "m spin" + (" rev" if rev else "")
    return (f'<g transform="translate({n(x)} {n(y)})"><g class="{cls}" style="--T:{T}s">'
            f'<circle r="{n(rt)}" fill="none"/><path d="{d}" fill="{fill}" fill-rule="evenodd"/></g></g>')


def kf(name, body):
    return f"@keyframes {name}{{{body}}}"


BASE_CSS = """
.m{transform-box:fill-box;transform-origin:center}
@keyframes spin{to{transform:rotate(360deg)}}
.spin{animation:spin var(--T,30s) linear infinite}
.rev{animation-direction:reverse}
@keyframes sig{0%{transform:scale(1);opacity:.7}100%{transform:scale(var(--S,3.4));opacity:0}}
.sig{animation:sig 4.2s cubic-bezier(.16,1,.3,1) infinite}
@keyframes breathe{0%,100%{opacity:.45}50%{opacity:1}}
.breathe{animation:breathe 3s ease-in-out infinite}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(8px)}}
.nudge{animation:nudge 1.8s ease-in-out infinite}
@keyframes rise{from{transform:translateY(110px);opacity:0}to{transform:none;opacity:1}}
.rise{animation:rise .9s cubic-bezier(.16,1,.3,1) var(--d,0s) both}
@keyframes draw{0%{stroke-dashoffset:1;stroke-opacity:1}70%{stroke-dashoffset:0;stroke-opacity:1}100%{stroke-dashoffset:0;stroke-opacity:0}}
@keyframes fillin{from{fill-opacity:0}to{fill-opacity:1}}
.wm{stroke-dasharray:1;stroke-opacity:0;stroke-width:2.2;animation:draw 1.5s cubic-bezier(.4,0,.2,1) var(--d,0s) both,fillin .7s ease-out calc(var(--d,0s) + .9s) both}
@keyframes ecg{from{stroke-dashoffset:22}to{stroke-dashoffset:-78}}
.ecg{animation:ecg 3s linear infinite}
@keyframes marq{to{transform:translateX(var(--W))}}
.marq{animation:marq var(--T,34s) linear infinite}
@keyframes pop{from{opacity:.35;transform:scale(.78)}to{opacity:1;transform:none}}
.pop{animation:pop .6s cubic-bezier(.16,1,.3,1) var(--d,0s) both}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
.float{animation:float 4s ease-in-out var(--d,0s) infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def svg(w, h, body, defs="", css="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}" role="img"><title>{esc(label)}</title><defs><style>{BASE_CSS}{css}</style>{defs}</defs>{body}</svg>')


def smil_window(i, dur=8.0, step=2.0):
    t0 = i * step / dur
    a, b, c = t0, t0 + 0.25 / dur, t0 + (step - 0.25) / dur
    e = t0 + step / dur
    kt = [0, a, b, c, e, 1]
    vals = "0;0;1;1;0;0"
    return (f'<animate attributeName="opacity" values="{vals}" keyTimes="{";".join(f"{min(x, 1):.4f}" for x in kt)}" '
            f'dur="{dur}s" repeatCount="indefinite"/>')


ARROW = "M0 0H20M12 -8L20 0L12 8"


# ------------------------------------------------------------------ icons
def icon(key, t, size=38):
    ic = ICONS[key]
    k = size / ic["vb"]
    bg = t["surface-2"]
    out = ""
    for p in ic["paths"]:
        f = norm(p["fill"]) if p["fill"] else t["fg"]
        if lum(f) < 0.04:
            f = t["fg"]
        elif lum(f) <= 0.85:
            f = legible(f, bg, 3.0)
        out += f'<path d="{p["d"]}" fill="{f}"/>'
    return f'<g transform="translate({n(-size / 2)} {n(-size / 2)}) scale({k:.5f})">{out}</g>'


# ------------------------------------------------------------------ hero
def hero(t):
    W, H, cx, cy = 1200, 600, 970, 284
    css = ""
    defs = (f'<clipPath id="hc"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
            f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="{t["wire"]}"/></pattern>'
            f'<radialGradient id="fade" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="470"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
            f'<mask id="fm"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'
            f'<clipPath id="t1"><rect x="0" y="306" width="800" height="56"/></clipPath>'
            f'<clipPath id="t2"><rect x="0" y="356" width="800" height="56"/></clipPath>')

    def node(kind):
        if kind == "mech":
            return (f'<rect x="-32" y="-32" width="64" height="64" rx="16" fill="{t["mech"]}"/>'
                    + gear(10, 13, 2.6, t["on-mech"], 0, 14))
        if kind == "med":
            e = "M-22 0L-10 0L-6-9L0 10L4-3L8 0L22 0"
            return (f'<rect x="-32" y="-32" width="64" height="64" rx="16" fill="{t["med"]}"/>'
                    f'<path d="{e}" fill="none" stroke="{t["on-med"]}" stroke-opacity=".3" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
                    f'<path class="ecg" d="{e}" pathLength="100" fill="none" stroke="{t["on-med"]}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="22 78"/>')
        return (f'<rect x="-28" y="-28" width="56" height="56" rx="14" fill="{t["wire"]}"/>'
                f'<path class="breathe" d="M-11 0H11M0-11V11" stroke="{t["fg"]}" stroke-width="4" stroke-linecap="round"/>')

    def ring(r, T, ccw, items):
        inner = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["wire"]}" stroke-width="3" stroke-dasharray="2 11" stroke-linecap="round"/>')
        for kind, ang in items:
            a = math.radians(ang)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if kind == "dot":
                inner += f'<circle cx="{n(x)}" cy="{n(y)}" r="4.5" fill="{t["accent"]}"/>'
            else:
                cls = "m spin" + ("" if ccw else " rev")
                inner += (f'<g transform="translate({n(x)} {n(y)})"><g class="{cls}" style="--T:{T}s">'
                          f'<circle r="42" fill="none"/>{node(kind)}</g></g>')
        cls = "spin" + (" rev" if ccw else "")
        return f'<g class="{cls}" style="--T:{T}s;transform-origin:{cx}px {cy}px">{inner}</g>'

    rings = (ring(92, 70, True, [("plus", 205), ("dot", 20), ("dot", 110)])
             + ring(146, 96, False, [("mech", -58), ("dot", 60), ("dot", 150), ("dot", 250)])
             + ring(190, 130, True, [("med", 28), ("dot", 130), ("dot", 210), ("dot", 300)]))
    sweep = ""
    R, slices, span = 236, 16, 70
    for i in range(slices):
        a1, a2 = math.radians(-span + i * span / slices), math.radians(-span + (i + 1) * span / slices)
        sweep += (f'<path d="M{cx} {cy}L{n(cx + R * math.cos(a1))} {n(cy + R * math.sin(a1))}A{R} {R} 0 0 1 {n(cx + R * math.cos(a2))} {n(cy + R * math.sin(a2))}Z" '
                  f'fill="{t["accent"]}" fill-opacity="{0.015 + 0.17 * ((i + 1) / slices) ** 2:.3f}"/>')
    sweep = f'<g class="spin" style="--T:9s;transform-origin:{cx}px {cy}px">{sweep}</g>'
    hub = "".join(f'<circle class="m sig" cx="{cx}" cy="{cy}" r="46" fill="none" stroke="{t["accent"]}" stroke-width="3" style="animation-delay:-{d}s"/>' for d in (0, 1.4, 2.8))
    hub += (f'<circle cx="{cx}" cy="{cy}" r="46" fill="{t["accent"]}"/>'
            f'<g class="spin" style="--T:12s;transform-origin:{cx}px {cy}px"><circle cx="{cx}" cy="{cy}" r="60" fill="none" stroke="{t["accent"]}" stroke-width="4" stroke-linecap="round" stroke-dasharray="40 148.5"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="17" fill="{t["on-accent"]}"/><circle class="breathe" cx="{cx}" cy="{cy}" r="6" fill="{t["accent"]}"/>')

    # wordmark: drawn on, then filled
    items, w100 = layout("Novotia", 800, 100, -0.03)
    size = 640 / (w100 / 100)
    items, ww = layout("Novotia", 800, size, -0.03)
    k, base = size / 1000, 292
    wm = ""
    for i, (ch, ix, g) in enumerate(items):
        wm += (f'<path class="wm" pathLength="1" d="{xf(g, k, 64 + ix, base)}" fill="{t["fg"]}" stroke="{t["fg"]}" style="--d:{i * 0.09:.2f}s"/>')
    dot_r = size * 0.085
    wm += f'<circle class="m pop" cx="{n(64 + ww + size * 0.1)}" cy="{n(base - dot_r)}" r="{n(dot_r)}" fill="{t["accent"]}" style="--d:1.5s"/>'

    l1, _ = ptext("AI agents that do real work", 600, 38, 66, 346, t["fg"], -0.01)
    l2, _ = ptext("in real industries.", 600, 38, 66, 392, t["fg-muted"], -0.01)
    tag = (f'<g clip-path="url(#t1)"><g class="rise" style="--d:.7s">{l1}</g></g>'
           f'<g clip-path="url(#t2)"><g class="rise" style="--d:.85s">{l2}</g></g>')

    pill = (f'<rect x="64" y="440" width="478" height="46" rx="23" fill="{t["surface-2"]}"/>'
            f'<circle class="m sig" cx="92" cy="463" r="6" fill="none" stroke="{t["accent"]}" stroke-width="2" style="--S:2.6"/>'
            f'<circle cx="92" cy="463" r="6" fill="{t["accent"]}"/>'
            f'<text x="112" y="470" font-size="20" font-weight="600" fill="{t["fg"]}">Now building: Mechanical and Medical</text>')

    # ticker
    x, parts = 0.0, ""
    for it in ("AGENTIC AI", "MOBILE", "WEB3", "SOFTWARE", "MECHANICAL", "MEDICAL"):
        p, w = ptext(it, 600, 20, x, 575, t["fg-muted"], 0.14)
        parts += p
        x += w + 36
        parts += f'<circle cx="{n(x - 18)}" cy="567" r="4" fill="{t["accent"]}"/>'
    W1 = x
    defs += f'<g id="ts">{parts}</g>'
    ticker = (f'<rect y="536" width="{W}" height="64" fill="{t["surface-2"]}"/>'
              f'<g class="marq" style="--W:-{n(W1)}px;--T:36s"><use href="#ts"/><use href="#ts" x="{n(W1)}"/><use href="#ts" x="{n(2 * W1)}"/></g>')

    body = (f'<g clip-path="url(#hc)"><rect width="{W}" height="{H}" fill="{t["surface"]}"/>'
            f'<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#fm)"/>'
            f'{sweep}{rings}{hub}{wm}{tag}{pill}{ticker}</g>')
    return svg(W, H, body, defs, css, "Novotia. AI agents that do real work in real industries.")


# ------------------------------------------------------------------ domains
def domains(t):
    W, H, fw, gap = 1200, 340, 384, 24
    tiles = [
        (t["mech"], t["on-mech"], "Mechanical", ("Agents for industrial and", "engineering workflows."), "In build"),
        (t["med"], t["on-med"], "Medical", ("Agents that support", "healthcare workflows."), "In build"),
        (t["surface-2"], t["fg"], "Your industry", ("Bring a real problem and", "we’ll scope the agent."), "Open"),
    ]
    m = 6.2
    scenes = [
        (gear(16, 16 * m / 2, m, tiles[0][1], 0, 26, False, 92, 112)
         + gear(10, 10 * m / 2, m, tiles[0][1], 162, 16.25, True, 172.6, 112)
         + gear(22, 22 * m / 2, m, tiles[0][1], 189.8, 35.75, False, 266.9, 142.7)),
    ]
    beat = [(0, 0), (34, 0), (42, -10), (50, 0), (64, 0), (70, 8), (78, -56), (88, 40), (94, 0), (112, 0), (124, -16), (138, 0), (160, 0)]
    pts = [(32 + bx + off, 130 + by) for off in (0, 160) for bx, by in beat]
    ed = "M" + "L".join(f"{x} {y}" for x, y in pts)
    ink = tiles[1][1]
    scenes.append(f'<path d="{ed}" fill="none" stroke="{ink}" stroke-opacity=".28" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                  f'<path class="ecg" d="{ed}" pathLength="100" fill="none" stroke="{ink}" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="22 78" style="animation-duration:3.4s"/>')
    ox = 192
    o = ""
    for r, T, rev, ang in ((34, 26, False, 30), (66, 40, True, 150), (98, 58, False, 260)):
        a = math.radians(ang)
        cls = "m spin" + (" rev" if rev else "")
        o += (f'<g class="{cls}" style="--T:{T}s"><circle cx="{ox}" cy="128" r="{r + 8}" fill="none"/>'
              f'<circle cx="{ox}" cy="128" r="{r}" fill="none" stroke="{t["wire"]}" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round"/>'
              f'<circle cx="{n(ox + r * math.cos(a))}" cy="{n(128 + r * math.sin(a))}" r="5.5" fill="{t["accent"]}"/></g>')
    o += f'<path class="breathe" d="M{ox - 14} 128H{ox + 14}M{ox} 114V142" stroke="{t["fg"]}" stroke-width="5" stroke-linecap="round"/>'
    scenes.append(o)
    b = ""
    for i, ((bg, ink, title, sub, status), sc) in enumerate(zip(tiles, scenes)):
        x = i * (fw + gap)
        chip_bg, chip_tx = (ink, bg) if i < 2 else (t["fg"], t["surface-2"])
        b += (f'<g transform="translate({x} 0)"><rect width="{fw}" height="{H}" rx="16" fill="{bg}"/>{sc}'
              f'<rect x="{fw - 32 - 104}" y="28" width="104" height="36" rx="18" fill="{chip_bg}"/>'
              f'<text x="{fw - 32 - 52}" y="52" text-anchor="middle" font-size="16" font-weight="700" fill="{chip_tx}">{status}</text>'
              f'<text x="32" y="266" font-size="40" font-weight="800" letter-spacing="-1" fill="{ink}">{title}</text>'
              f'<text x="32" y="298" font-size="18" fill="{ink}">{sub[0]}</text><text x="32" y="322" font-size="18" fill="{ink}">{sub[1]}</text></g>')
    return svg(W, H, b, "", "", "Mechanical and medical are in build. Your industry is open.")


# ------------------------------------------------------------------ capabilities
def capabilities(t):
    W, H, cw, gap = 1200, 290, 384, 24
    css = ""
    # --- agentic: hub with six satellites, pulses travel out in turn
    hub, R = (192, 92), 64
    css += kf("pk", "0%{transform:translate(0,0);opacity:0}2%{opacity:1}14%{transform:translate(var(--dx),var(--dy));opacity:1}16%,100%{transform:translate(var(--dx),var(--dy));opacity:0}")
    css += kf("fk", "0%,12%{opacity:0}14%{opacity:1}34%,100%{opacity:0}")
    s1 = ""
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        x, y = hub[0] + R * math.cos(a), hub[1] + R * math.sin(a)
        s1 += f'<path d="M{hub[0]} {hub[1]}L{n(x)} {n(y)}" stroke="{t["wire"]}" stroke-width="4" stroke-linecap="round"/>'
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        x, y = hub[0] + R * math.cos(a), hub[1] + R * math.sin(a)
        s1 += (f'<circle cx="{n(x)}" cy="{n(y)}" r="10" fill="{t["wire"]}"/>'
               f'<circle cx="{n(x)}" cy="{n(y)}" r="10" fill="{t["accent"]}" style="opacity:0;animation:fk 6s linear {k}s infinite both"/>'
               f'<circle cx="{hub[0]}" cy="{hub[1]}" r="5" fill="{t["accent"]}" style="--dx:{n(x - hub[0])}px;--dy:{n(y - hub[1])}px;opacity:0;animation:pk 6s linear {k}s infinite both"/>')
    s1 += (f'<circle class="m sig" cx="{hub[0]}" cy="{hub[1]}" r="18" fill="none" stroke="{t["accent"]}" stroke-width="3" style="--S:2.2"/>'
           f'<circle cx="{hub[0]}" cy="{hub[1]}" r="18" fill="{t["accent"]}"/><circle cx="{hub[0]}" cy="{hub[1]}" r="6" fill="{t["on-accent"]}"/>')
    # --- mobile and web3: phone sends a packet down a chain of blocks
    css += kf("mv", "0%{transform:translateX(0);opacity:0}5%{opacity:1}85%{transform:translateX(222px);opacity:1}92%,100%{transform:translateX(222px);opacity:0}")
    s2 = (f'<rect x="46" y="30" width="58" height="124" rx="13" fill="none" stroke="{t["fg-muted"]}" stroke-width="5"/>'
          f'<rect x="60" y="48" width="30" height="8" rx="4" fill="{t["wire"]}"/><rect x="60" y="64" width="30" height="8" rx="4" fill="{t["wire"]}"/>'
          f'<rect x="60" y="80" width="20" height="8" rx="4" fill="{t["wire"]}"/>'
          f'<rect x="60" y="112" width="30" height="26" rx="8" fill="{t["accent"]}" class="breathe"/>')
    for i, bx in enumerate((160, 232, 304)):
        if i < 2:
            s2 += f'<path d="M{bx + 44} 92H{bx + 72}" stroke="{t["wire"]}" stroke-width="5" stroke-linecap="round"/>'
        tt = (33, 59, 84)[i]
        css += kf(f"bk{i}", f"0%,{tt - 2}%{{opacity:0}}{tt}%{{opacity:1}}{min(tt + 20, 99)}%,100%{{opacity:0}}")
        s2 += (f'<rect x="{bx}" y="70" width="44" height="44" rx="11" fill="{t["wire"]}"/>'
               f'<rect x="{bx}" y="70" width="44" height="44" rx="11" fill="{t["accent"]}" style="opacity:0;animation:bk{i} 4s linear infinite"/>')
    s2 += f'<circle cx="104" cy="92" r="6" fill="{t["accent"]}" style="opacity:0;animation:mv 4s linear infinite"/>'
    # --- software: a request passes down through the layers and back
    css += kf("l0", "0%,18%{opacity:1}22%,86%{opacity:0}90%,100%{opacity:1}")
    css += kf("l1", "0%,20%{opacity:0}24%,40%{opacity:1}44%,62%{opacity:0}66%,84%{opacity:1}88%,100%{opacity:0}")
    css += kf("l2", "0%,40%{opacity:0}44%,62%{opacity:1}66%,100%{opacity:0}")
    s3 = ""
    for i, lab in enumerate(("API", "Services", "Data")):
        y = 22 + i * 48
        s3 += (f'<rect x="48" y="{y}" width="288" height="38" rx="10" fill="{t["wire"]}"/>'
               f'<text x="68" y="{y + 25}" font-size="18" font-weight="600" fill="{t["fg"]}">{lab}</text>'
               f'<g style="opacity:0;animation:l{i} 5s linear infinite"><rect x="48" y="{y}" width="288" height="38" rx="10" fill="{t["accent"]}"/>'
               f'<text x="68" y="{y + 25}" font-size="18" font-weight="600" fill="{t["on-accent"]}">{lab}</text></g>')
    cards = [("Agentic AI", "Plan, use tools, finish the task", s1), ("Mobile and Web3", "Apps and on-chain products", s2), ("Software systems", "Backends, APIs, cloud", s3)]
    b = ""
    for i, (title, sub, sc) in enumerate(cards):
        b += (f'<g transform="translate({i * (cw + gap)} 0)"><rect width="{cw}" height="{H}" rx="16" fill="{t["surface-2"]}"/>{sc}'
              f'<text x="32" y="236" font-size="30" font-weight="800" letter-spacing="-.5" fill="{t["fg"]}">{title}</text>'
              f'<text x="32" y="266" font-size="18" fill="{t["fg-muted"]}">{sub}</text></g>')
    return svg(W, H, b, "", css, "Agentic AI, mobile and Web3, software systems.")


# ------------------------------------------------------------------ loop
def loop(t):
    W, H, bw, gap, bh = 1200, 506, 264, 48, 140
    steps = [("Sense", "Read the real data"), ("Reason", "Plan the next step"), ("Act", "Use tools, do the work"), ("Verify", "Check before it ships")]
    b = ""
    for i, (title, sub) in enumerate(steps):
        x = i * (bw + gap)
        b += (f'<g transform="translate({x} 0)"><rect width="{bw}" height="{bh}" rx="16" fill="{t["surface-2"]}"/>'
              f'<text x="24" y="66" font-size="32" font-weight="800" fill="{t["fg"]}">{title}</text>'
              f'<text x="24" y="102" font-size="18" fill="{t["fg-muted"]}">{sub}</text>'
              f'<g opacity="0">{smil_window(i)}<rect width="{bw}" height="{bh}" rx="16" fill="{t["accent"]}"/>'
              f'<text x="24" y="66" font-size="32" font-weight="800" fill="{t["on-accent"]}">{title}</text>'
              f'<text x="24" y="102" font-size="18" fill="{t["on-accent"]}">{sub}</text></g></g>')
        if i < 3:
            cx = x + bw + gap / 2
            b += f'<path d="M{cx - 7} {bh / 2 - 14}L{cx + 7} {bh / 2}L{cx - 7} {bh / 2 + 14}" fill="none" stroke="{t["fg-muted"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    cxs = [bw / 2 + i * (bw + gap) for i in range(4)]
    ty = 176
    b += f'<path d="M{cxs[0]} {ty}H{cxs[3]}" stroke="{t["wire"]}" stroke-width="6" stroke-linecap="round"/>'
    for c in cxs:
        b += f'<circle cx="{c}" cy="{ty}" r="9" fill="{t["surface"]}" stroke="{t["wire"]}" stroke-width="5"/>'
    kt = [0, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 8]
    kp = [0, 0, 1 / 3, 1 / 3, 2 / 3, 2 / 3, 1, 1]
    mp = f'M{cxs[0]},{ty}H{cxs[3]}'
    b += (f'<circle r="9" fill="{t["accent"]}" opacity="0"><animateMotion dur="8s" repeatCount="indefinite" path="{mp}" '
          f'keyPoints="{";".join(f"{v:.4f}" for v in kp)}" keyTimes="{";".join(f"{v / 8:.4f}" for v in kt)}" calcMode="linear"/>'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.03;.9;1" dur="8s" repeatCount="indefinite"/></circle>')
    b += f'<text x="{W / 2}" y="222" text-anchor="middle" font-size="18" fill="{t["fg-muted"]}">Repeat until the result holds up</text>'
    # trace
    py = 252
    b += (f'<rect y="{py}" width="{W}" height="{H - py}" rx="16" fill="{t["surface-2"]}"/>'
          f'<text x="32" y="{py + 42}" font-size="18" font-weight="600" fill="{t["fg-muted"]}">An example run</text>')
    lines = [("Sense", "Pull the latest data from the client’s systems"),
             ("Reason", "Break the task into steps and pick the right tool"),
             ("Act", "Run the steps: call the API, update the record"),
             ("Verify", "Check the result against the request before it ships")]
    defs = ""
    for i, (lab, txt) in enumerate(lines):
        y = py + 100 + i * 46
        s_, e_, h_ = (i * 2 + 0.15) / 8, (i * 2 + 1.35) / 8, 7.6 / 8
        defs += (f'<clipPath id="cl{i}"><rect x="188" y="{y - 26}" width="800" height="38">'
                 f'<animate attributeName="width" values="0;0;800;800;0" keyTimes="0;{s_:.4f};{e_:.4f};{h_:.4f};1" dur="8s" repeatCount="indefinite"/></rect></clipPath>')
        b += (f'<text x="32" y="{y}" font-size="21" font-weight="800" fill="{t["fg"]}">{lab}</text>'
              f'<text x="188" y="{y}" font-size="21" font-family="{MONO}" fill="{t["fg"]}" clip-path="url(#cl{i})">{esc(txt)}</text>'
              f'<path d="M{W - 70} {y - 8}l8 9 17-20" fill="none" stroke="{t["accent"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0">'
              f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{e_:.4f};{e_ + .03:.4f};{h_:.4f};1" dur="8s" repeatCount="indefinite"/></path>')
    return svg(W, H, b, defs, "", "Sense, reason, act, verify. Repeat until the result holds up.")


# ------------------------------------------------------------------ stack
def stack(t):
    groups = [("Languages", ["javascript", "python", "kotlin", "cpp", "csharp", "java"]),
              ("Frontend and 3D", ["react", "threejs", "angular", "html", "css", "tailwind"]),
              ("Cloud and infra", ["gcp", "aws", "cloudflare", "docker", "linux"]),
              ("Data and backend", ["postgres", "mongodb", "redis", "supabase", "firebase"])]
    W, H, cw, gap = 1200, 262, 282, 24
    b = ""
    for gi, (title, keys) in enumerate(groups):
        b += (f'<g transform="translate({gi * (cw + gap)} 0)"><rect width="{cw}" height="{H}" rx="16" fill="{t["surface"]}"/>'
              f'<text x="31" y="56" font-size="22" font-weight="700" fill="{t["fg"]}">{title}</text>')
        for i, key in enumerate(keys):
            col, row = i % 3, i // 3
            x, y = 31 + col * 78 + 32, 90 + row * 78 + 32
            idx = gi * 6 + i
            b += (f'<g transform="translate({x} {y})"><g class="float" style="--d:{(idx * 0.37) % 4:.2f}s"><g class="m pop" style="--d:{gi * 0.12 + i * 0.07:.2f}s">'
                  f'<rect x="-32" y="-32" width="64" height="64" rx="16" fill="{t["surface-2"]}"/>{icon(key, t)}</g></g></g>')
        b += "</g>"
    return svg(W, H, b, "", "", "Stack: JavaScript, Python, Kotlin, C++, C#, Java, React, Three.js, Angular, HTML, CSS, Tailwind, GCP, AWS, Cloudflare, Docker, Linux, PostgreSQL, MongoDB, Redis, Supabase, Firebase.")


# ------------------------------------------------------------------ repo cards
def repo(name):
    def fn(t):
        W, H = 588, 176
        b = (f'<rect width="{W}" height="{H}" rx="16" fill="{t["surface"]}"/>'
             f'<text x="32" y="82" font-size="34" font-weight="800" letter-spacing="-.5" fill="{t["fg"]}">{name}</text>'
             f'<text x="32" y="116" font-size="18" fill="{t["fg-muted"]}">github.com/NovotiaGng/{name}</text>'
             f'<g transform="translate({W - 72} 132)"><path class="nudge" d="{ARROW}" fill="none" stroke="{t["accent"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g>')
        return svg(W, H, b, "", "", f"{name} on GitHub")
    return fn


# ------------------------------------------------------------------ cta
def cta(t):
    W, H, cx, cy = 1200, 440, 1010, 220
    a, on = t["accent"], t["on-accent"]
    lines = ptext("Have a real problem?", 800, 66, 56, 150, on, -0.02)[0] + ptext("We’ll build the agent.", 800, 66, 56, 228, on, -0.02)[0]

    def ring(r, T, ccw, ang):
        cls = "spin" + (" rev" if ccw else "")
        s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["accent-wire"]}" stroke-width="3" stroke-dasharray="2 11" stroke-linecap="round"/>'
        for g_, rad in ang:
            q = math.radians(g_)
            s += f'<circle cx="{n(cx + r * math.cos(q))}" cy="{n(cy + r * math.sin(q))}" r="{rad}" fill="{on}"/>'
        return f'<g class="{cls}" style="--T:{T}s;transform-origin:{cx}px {cy}px">{s}</g>'

    scene = (ring(84, 60, True, [(200, 13), (20, 6)]) + ring(134, 84, False, [(-50, 16), (110, 7), (250, 7)]) + ring(184, 120, True, [(30, 12), (160, 7), (290, 9)]))
    scene += "".join(f'<circle class="m sig" cx="{cx}" cy="{cy}" r="40" fill="none" stroke="{on}" stroke-width="3" style="animation-delay:-{d}s"/>' for d in (0, 1.4, 2.8))
    scene += f'<circle cx="{cx}" cy="{cy}" r="40" fill="{on}"/><circle class="breathe" cx="{cx}" cy="{cy}" r="14" fill="{a}"/>'
    body = (f'<clipPath id="cc"><rect width="{W}" height="{H}" rx="16"/></clipPath><g clip-path="url(#cc)"><rect width="{W}" height="{H}" fill="{a}"/>{scene}{lines}'
            f'<text x="58" y="290" font-size="24" fill="{on}">Tell us the workflow. We’ll scope the agent.</text>'
            f'<rect x="56" y="330" width="340" height="68" rx="34" fill="{on}"/>'
            f'<text x="90" y="373" font-size="22" font-weight="700" fill="{a}">Start a conversation</text>'
            f'<g transform="translate(346 364)"><path class="nudge" d="{ARROW}" fill="none" stroke="{a}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
            f'<text x="424" y="372" font-size="22" font-weight="600" fill="{on}">novotiaproducts@gmail.com</text></g>')
    return svg(W, H, body, "", "", "Have a real problem? We’ll build the agent. novotiaproducts@gmail.com")


# ------------------------------------------------------------------ build
BUILDERS = [("header", hero), ("domains", domains), ("capabilities", capabilities), ("loop", loop), ("stack", stack),
            ("cta", cta), ("repo-meshmend", repo("MeshMend")), ("repo-novotiagng", repo("NovotiaGng"))]

if __name__ == "__main__":
    for old in OUT.glob("*-dark.svg"):
        old.unlink()
    for old in OUT.glob("*-light.svg"):
        old.unlink()
    total = 0
    for mode in ("dark", "light"):
        t = theme(mode)
        for name, fn in BUILDERS:
            s = fn(t)
            (OUT / f"{name}-{mode}.svg").write_text(s)
            total += len(s)
    print(f"generated {len(BUILDERS) * 2} svgs, {total // 1024} KB total in {OUT}")
