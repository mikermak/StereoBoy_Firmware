"""Colour artwork like colorart.py, plus Retroid branding overlays (logo + credit line)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import colorart as ca

LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "artwork", "retroid_logo.png")
FONT = r"C:\Windows\Fonts\arialbd.ttf"  # any bold TTF works
WHITE = (245, 245, 240, 255)

# (layer, kind, payload, centre x mm, centre y mm from bottom, width or font-height mm)
# B-layer art is in top view, so face-side items are mirrored to read correctly from the face.
OVERLAYS = {
    "hoofdprint": [
        ("F", "logo", LOGO, 40.0, 38.0, 38.0),
        ("F", "text", "based on StereoBoy by iamericmin", 40.0, 31.8, 1.3),
        ("B", "logo", LOGO, 9.6, 114.8, 15.0),
    ],
}


def place(art, kind, payload, cx, cy_bottom, size, board_h_mm, mirror):
    px = ca.PX
    if kind == "logo":
        logo = Image.open(payload).convert("RGBA")
        w = int(size * px); h = int(w * logo.height / logo.width)
        im = logo.resize((w, h), Image.LANCZOS)
    else:
        font = ImageFont.truetype(FONT, int(size * px))
        bbox = font.getbbox(payload)
        im = Image.new("RGBA", (bbox[2] - bbox[0] + 4, bbox[3] - bbox[1] + 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((2 - bbox[0], 2 - bbox[1]), payload, font=font, fill=WHITE)
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    x = int(cx * px - im.width / 2) + ca.PAD
    y = int((board_h_mm - cy_bottom) * px - im.height / 2) + ca.PAD
    art.alpha_composite(im, (x, y))


def side(prefix, layer, size, inside, h_mm, overlays):
    tracks = ca.stroked_only(f"{prefix}-{layer}_Cu.svg", size)
    mask_open = ca.raster(f"{prefix}-{layer}_Mask.svg", size).filter(ImageFilter.MaxFilter(5))
    silk = ca.raster(f"{prefix}-{layer}_Silkscreen.svg", size)
    art = Image.new("RGBA", size, (0, 0, 0, 0))
    art.paste(Image.new("RGBA", size, ca.BLACK), (0, 0), inside)
    art.paste(Image.new("RGBA", size, ca.RED), (0, 0), ImageChops.multiply(tracks, inside))
    art.putalpha(ImageChops.subtract(art.getchannel("A"), silk))          # white silkscreen
    for lay, kind, payload, cx, cy, sz in overlays:
        if lay == layer:
            place(art, kind, payload, cx, cy, sz, h_mm, mirror=(layer == "B"))
    art.putalpha(ImageChops.multiply(art.getchannel("A"), inside))        # stay inside the outline
    art.putalpha(ImageChops.subtract(art.getchannel("A"), mask_open))     # pads stay bare (gold)
    preview = Image.new("RGBA", size, (0, 0, 0, 0))
    preview.paste(Image.new("RGBA", size, (245, 245, 240, 255)), (0, 0), inside)
    preview.paste(Image.new("RGBA", size, (212, 175, 55, 255)), (0, 0), ImageChops.multiply(mask_open, inside))
    preview.alpha_composite(art)
    return art, preview


if __name__ == "__main__":
    svgdir, prefix, outdir, tag = sys.argv[1:5]
    pre = os.path.join(svgdir, prefix)
    _, w, h = ca.load(pre + "-Edge_Cuts.svg")
    size = (int(w * ca.PX) + 2 * ca.PAD, int(h * ca.PX) + 2 * ca.PAD)
    inside = ca.board_mask(pre + "-Edge_Cuts.svg", size)
    for layer, name in (("F", "boven"), ("B", "onder")):
        art, prev = side(pre, layer, size, inside, h, OVERLAYS.get(tag, []))
        art.crop((ca.PAD, ca.PAD, size[0] - ca.PAD, size[1] - ca.PAD)).save(
            os.path.join(outdir, f"kleur_{tag}_{name}_{w:.2f}x{h:.2f}mm_1200dpi.png"), dpi=(ca.DPI, ca.DPI))
        prev = prev.convert("RGB").resize((size[0] // 4, size[1] // 4), Image.LANCZOS)
        if layer == "B":
            prev = prev.transpose(Image.FLIP_LEFT_RIGHT)
        prev.save(os.path.join(outdir, f"voorbeeld_{tag}_{name}.png"))
    print("ok", size)
