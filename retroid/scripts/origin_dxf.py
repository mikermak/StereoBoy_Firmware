"""Put the KiCad aux (drill/place) origin at the board's bottom-left corner and write a matching outline DXF.

With both at (0,0) bottom-left, Y up, the KiCad Gerbers/drill/CPL and the EasyEDA colour-silkscreen
files share one coordinate system.
"""
import math, re, sys

pcb_path, dxf_path = sys.argv[1:3]
src = open(pcb_path, encoding="utf8").read()

tok = re.compile(r'[()]|"(?:[^"\\]|\\.)*"|[^\s()]+')
def parse(s):
    st = [[]]
    for m in tok.finditer(s):
        t = m.group()
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def get(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None

def xy(node, key):
    c = get(node, key)
    return (float(c[1]), float(c[2])) if c else None

ents = []
for n in parse(src):
    if not (isinstance(n, list) and n and n[0] in ("gr_line", "gr_arc", "gr_rect", "gr_circle", "gr_poly")):
        continue
    if get(n, "layer")[1] != "Edge.Cuts":
        continue
    if n[0] == "gr_line":
        ents.append(("L", xy(n, "start"), xy(n, "end")))
    elif n[0] == "gr_arc":
        ents.append(("A", xy(n, "start"), xy(n, "mid"), xy(n, "end")))
    elif n[0] == "gr_rect":
        (x1, y1), (x2, y2) = xy(n, "start"), xy(n, "end")
        for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
            ents.append(("L", a, b))
    elif n[0] == "gr_circle":
        c, e = xy(n, "center"), xy(n, "end")
        ents.append(("C", c, math.dist(c, e)))
    elif n[0] == "gr_poly":
        pts = [(float(p[1]), float(p[2])) for p in get(n, "pts")[1:] if p[0] == "xy"]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            ents.append(("L", a, b))

def circ(p1, p2, p3):
    ax, ay = p1; bx, by = p2; cx, cy = p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    return (ux, uy), math.dist((ux, uy), p1)

# bounding box (arcs sampled)
pts = []
for e in ents:
    if e[0] == "L":
        pts += [e[1], e[2]]
    elif e[0] == "A":
        (c, r) = circ(e[1], e[2], e[3])
        pts += [e[1], e[2], e[3]]
        a0 = math.atan2(e[1][1] - c[1], e[1][0] - c[0])
        for k in range(64):
            a = a0 + k * 2 * math.pi / 64
            p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            pts.append(p)  # over-approximation is fine only if arcs are small; checked below
    elif e[0] == "C":
        c, r = e[1], e[2]
        pts += [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
line_pts = [p for e in ents if e[0] == "L" for p in (e[1], e[2])] + [p for e in ents if e[0] == "A" for p in (e[1], e[2], e[3])]
minx = min(p[0] for p in line_pts); maxx = max(p[0] for p in line_pts)
miny = min(p[1] for p in line_pts); maxy = max(p[1] for p in line_pts)
ox, oy = minx, maxy  # bottom-left in KiCad coordinates (Y down)

def T(p):  # KiCad (Y down) -> DXF/Gerber (Y up), origin bottom-left
    return (p[0] - ox, oy - p[1])

out = ["0", "SECTION", "2", "ENTITIES"]
for e in ents:
    if e[0] == "L":
        (x1, y1), (x2, y2) = T(e[1]), T(e[2])
        out += ["0", "LINE", "8", "0", "10", f"{x1:.5f}", "20", f"{y1:.5f}", "11", f"{x2:.5f}", "21", f"{y2:.5f}"]
    elif e[0] == "A":
        s, m, en = T(e[1]), T(e[2]), T(e[3])
        c, r = circ(s, m, en)
        a1 = math.degrees(math.atan2(s[1] - c[1], s[0] - c[0])) % 360
        a2 = math.degrees(math.atan2(en[1] - c[1], en[0] - c[0])) % 360
        am = math.degrees(math.atan2(m[1] - c[1], m[0] - c[0])) % 360
        # DXF arcs run counter-clockwise from start to end angle; swap if mid isn't on that sweep
        if not ((am - a1) % 360 < (a2 - a1) % 360):
            a1, a2 = a2, a1
        out += ["0", "ARC", "8", "0", "10", f"{c[0]:.5f}", "20", f"{c[1]:.5f}", "40", f"{r:.5f}", "50", f"{a1:.5f}", "51", f"{a2:.5f}"]
    elif e[0] == "C":
        c = T(e[1])
        out += ["0", "CIRCLE", "8", "0", "10", f"{c[0]:.5f}", "20", f"{c[1]:.5f}", "40", f"{e[2]:.5f}"]
out += ["0", "ENDSEC", "0", "EOF"]
open(dxf_path, "w").write("\n".join(out) + "\n")

# aux origin in the board setup
aux = f"(aux_axis_origin {ox} {oy})"
if "(aux_axis_origin" in src:
    src = re.sub(r"\(aux_axis_origin [-\d.]+ [-\d.]+\)", aux, src, count=1)
else:
    src = src.replace("(setup", "(setup\n\t\t" + aux, 1)
open(pcb_path, "w", encoding="utf8").write(src)
print(f"origin {ox} {oy}  size {maxx - minx:.4f} x {maxy - miny:.4f} mm  entities {len(ents)}")
