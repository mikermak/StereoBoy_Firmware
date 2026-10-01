"""Build JLC multi-colour silkscreen artwork (black board, red tracks) from KiCad SVG layer plots."""
import sys, os
import svgelements as se
from PIL import Image, ImageDraw, ImageFilter, ImageChops

DPI = 1200
PX = DPI / 25.4
PAD = 12
BLACK = (14, 14, 16, 255)
RED = (210, 30, 38, 255)


def load(path):
    svg = se.SVG.parse(path, reify=True, ppi=25.4)  # 1 user unit = 1 mm
    vb = svg.viewbox
    return svg, vb.width, vb.height


def to_px(x, y):
    return (x * PX + PAD, y * PX + PAD)


def pts_of(sub):
    pts = []
    for seg in sub:
        if isinstance(seg, se.Move):
            pts.append(to_px(seg.end.x, seg.end.y))
        elif isinstance(seg, (se.Line, se.Close)):
            if seg.end is not None:
                pts.append(to_px(seg.end.x, seg.end.y))
        else:
            n = max(6, int(seg.length() * PX / 4))
            for i in range(1, n + 1):
                p = seg.point(i / n)
                pts.append(to_px(p.x, p.y))
    return pts


def raster(path, size, want_fill=True, want_stroke=True):
    """Return an 'L' mask of everything drawn in an SVG layer plot."""
    svg, _, _ = load(path)
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    for el in svg.elements():
        if not isinstance(el, se.Shape):
            continue
        p = se.Path(el)
        fill = el.fill is not None and el.fill.value is not None and el.fill.alpha != 0
        sw = (el.stroke_width or 0) if (el.stroke is not None and el.stroke.value is not None) else 0
        for sub in p.as_subpaths():
            pts = pts_of(se.Path(sub))
            if len(pts) < 1:
                continue
            if fill and want_fill and len(pts) > 2:
                d.polygon(pts, fill=255)
            if sw > 0 and want_stroke:
                w = max(1, round(sw * PX))
                if len(pts) > 1:
                    d.line(pts, fill=255, width=w)
                r = w / 2
                for x, y in pts:
                    d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return im


def stroked_only(path, size):
    return raster(path, size, want_fill=False, want_stroke=True)


def board_mask(edge_svg, size):
    outline = raster(edge_svg, size, want_fill=False)
    filled = outline.copy()
    ImageDraw.floodfill(filled, (1, 1), 128)
    inside = filled.point(lambda v: 0 if v == 128 else 255)
    return inside


def side(prefix, layer, size, inside):
    tracks = stroked_only(f"{prefix}-{layer}_Cu.svg", size)
    mask_open = raster(f"{prefix}-{layer}_Mask.svg", size).filter(ImageFilter.MaxFilter(5))  # ~0.05 mm extra clearance
    silk = raster(f"{prefix}-{layer}_Silkscreen.svg", size)
    art = Image.new("RGBA", size, (0, 0, 0, 0))
    art.paste(Image.new("RGBA", size, BLACK), (0, 0), inside)
    art.paste(Image.new("RGBA", size, RED), (0, 0), ImageChops.multiply(tracks, inside))
    clear = ImageChops.lighter(mask_open, silk)
    art.putalpha(ImageChops.subtract(art.getchannel("A"), clear))
    preview = Image.new("RGBA", size, (0, 0, 0, 0))
    preview.paste(Image.new("RGBA", size, (245, 245, 240, 255)), (0, 0), inside)           # white solder mask
    preview.paste(Image.new("RGBA", size, (212, 175, 55, 255)), (0, 0), ImageChops.multiply(mask_open, inside))  # ENIG
    preview.alpha_composite(art)
    return art, preview


if __name__ == "__main__":
    svgdir, prefix, outdir, tag = sys.argv[1:5]
    pre = os.path.join(svgdir, prefix)
    _, w, h = load(pre + "-Edge_Cuts.svg")
    size = (int(w * PX) + 2 * PAD, int(h * PX) + 2 * PAD)
    inside = board_mask(pre + "-Edge_Cuts.svg", size)
    os.makedirs(outdir, exist_ok=True)
    for layer, name in (("F", "boven"), ("B", "onder")):
        try:
            art, prev = side(pre, layer, size, inside)
        except FileNotFoundError:
            continue
        # crop the working margin so the image is exactly the board's bounding box (w x h mm)
        art.crop((PAD, PAD, size[0] - PAD, size[1] - PAD)).save(os.path.join(outdir, f"kleur_{tag}_{name}_{w:.2f}x{h:.2f}mm_1200dpi.png"), dpi=(DPI, DPI))
        prev = prev.convert("RGB").resize((size[0] // 4, size[1] // 4), Image.LANCZOS)
        if layer == "B":  # show the bottom as you would look at it, not through the board
            prev = prev.transpose(Image.FLIP_LEFT_RIGHT)
        prev.save(os.path.join(outdir, f"voorbeeld_{tag}_{name}.png"))
        print(layer, size)
