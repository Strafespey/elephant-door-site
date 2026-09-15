"""Build the Elephant Door mark and the site's favicon set.

Usage, from the site root, with a Python 3 that has Pillow and numpy (the
Warlock venv does: `D:\\CursorProjects\\Warlock\\venv\\Scripts\\python.exe tools\\make_icon.py`):

    python tools/make_icon.py            # writes every file below
    python tools/make_icon.py --preview  # also writes tools/icon_preview.png (contact sheet)

Writes:

    assets/favicon.svg                   square, transparent outside the door
    assets/favicon.ico                   16 / 32 / 48 px, heavier lines at the small sizes
    assets/apple-touch-icon.png          180 px, opaque (iOS fills transparency with black)
    assets/logos/elephant-door-mark.svg  the mark at the concept's 123 x 199 proportions
    assets/logos/elephant-door-mark.png  the same, 1024 px tall, transparent outside the door

The design lives in this file.  Every path is the centreline of a stroke in
Alex's `concept logo no text.png` (Documents/Elephant Door), redrawn as cubic
Beziers on the concept's 123 x 199 pixel grid; the concept's lines are ~3 px
wide in that space, which is the `stroke` of the full-size mark.  The hollow
inside the curl of the trunk is the concept's U.

Rasters are rendered by headless Chrome or Edge (whichever is installed) at
4x the target size and downsampled with premultiplied alpha, so there are no
dark fringes around the white lines.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# ---- design (concept pixel grid, 123 x 199) --------------------------------

W, H = 123, 199
FRAME = dict(x=9, y=6, w=108, h=184)          # door frame centreline

HEAD = (
	"M 46 52 "
	"C 51 49 60 47.5 68 48.5 "      # dome top
	"C 74 49.5 78 53 78.5 59 "      # front corner of the dome
	"C 79 65 78.5 68 79.5 71 "      # face front going down
	"C 80.5 75 84 75.5 85.5 80 "    # jog into the hollow's left arm
	"C 86.5 86 86 93 88 97 "        # left arm descending
	"C 89.5 99.5 93 100 95.5 98.5 " # rounded bottom of the hollow
	"C 98 97 98.5 93 98.5 88 "      # turning up
	"C 98.5 78 98 70 96 62 "        # right arm going up
	"C 93.5 53 88 47 81 43 "        # inner edge of the trunk, arcing up-left
	"C 74 39 64 34.5 55 32.5 "      # toward the tip
	"C 50 31.5 46 29 47 24 "        # tip cap, lower half
	"C 48 19.5 53 18.5 58 19.5 "    # tip cap, upper half
	"C 67 21 75 24 82 28 "          # outer edge over the top
	"C 92 33 102 40 107 50 "        # turning down
	"C 110 58 111 72 111 86 "       # right side descending
	"C 111 98 109.5 108 102.5 114 " # bottom-right corner
	"C 97.5 117 90 117 83 117 "     # chin, back to the neck
	"C 83 132 86 152 90 172"        # neck going down
)

EAR = (
	"M 46 52 "
	"C 37 56 27 64 18 72 "          # top edge down-left
	"C 15.5 74.5 15.5 77 18 80 "    # rounded top-left corner, turning down
	"C 20.5 83.5 21 88 19 93 "      # slight inward tuck
	"C 17 98 15 104 15 112 "        # outer edge
	"C 15 121 16 129 20 133 "       # down to the bottom-left
	"C 26 138 36 138 44 135 "       # bottom of the lobe
	"C 50 132 53 126 53.5 119 "     # inner edge curving up
	"C 54 113 54 109 54 106"        # ends against the face
)

EYE = dict(cx=62, cy=73.5, rx=4.5, ry=5.8)

LINE = "#ffffff"
DOOR = "#000000"
SITE_BG = "#2a1c3a"                            # assets/site.css body background


def svg(stroke=3.0, square=False, pad=0, bg=None, door=DOOR, line=LINE):
	"""The mark as an SVG string.

	stroke  line weight in design units (3 = the concept's weight)
	square  pad the viewBox out to a square, mark centred (favicons)
	pad     margin around the frame, design units
	bg      opaque background colour, or None for transparent
	door    fill inside the door frame, or None
	"""
	vw, vh = W + 2 * pad, H + 2 * pad
	ox, oy = pad, pad
	if square:
		side = max(vw, vh)
		ox += (side - vw) / 2
		oy += (side - vh) / 2
		vw = vh = side
	f = FRAME
	r = stroke / 2
	out = [
		f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:g} {vh:g}" '
		f'width="{vw:g}" height="{vh:g}">'
	]
	if bg:
		out.append(f'<rect width="100%" height="100%" fill="{bg}"/>')
	out.append(f'<g transform="translate({ox:g} {oy:g})">')
	if door:
		out.append(
			f'<rect x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{r:g}" fill="{door}"/>'
		)
	out.append(
		f'<g fill="none" stroke="{line}" stroke-width="{stroke:g}" '
		'stroke-linecap="round" stroke-linejoin="round">'
	)
	out.append(f'<rect x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{r:g}"/>')
	out.append(f'<path d="{HEAD}"/>')
	out.append(f'<path d="{EAR}"/>')
	out.append("</g>")
	e = EYE
	out.append(f'<ellipse cx="{e["cx"]}" cy="{e["cy"]}" rx="{e["rx"]}" ry="{e["ry"]}" fill="{line}"/>')
	out.append("</g></svg>")
	return "\n".join(out) + "\n"


# ---- rasterising -----------------------------------------------------------

BROWSERS = [
	r"C:\Program Files\Google\Chrome\Application\chrome.exe",
	r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
	r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
	r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
	for p in BROWSERS:
		if os.path.exists(p):
			return p
	for name in ("chrome", "google-chrome", "chromium", "msedge"):
		p = shutil.which(name)
		if p:
			return p
	sys.exit("no Chrome or Edge found; install one or add its path to BROWSERS")


def render(svg_text, width, height, browser, workdir):
	"""Rasterise an SVG string to an RGBA image of exactly width x height."""
	page = Path(workdir) / "page.html"
	shot = Path(workdir) / "shot.png"
	# The SVG's own width/height are its viewBox; the stylesheet scales it to the div.
	page.write_text(
		'<!doctype html><html><head><style>svg{width:100%;height:100%;display:block}</style></head>'
		'<body style="margin:0;background:transparent">'
		f'<div style="width:{width}px;height:{height}px">{svg_text}</div></body></html>',
		encoding="utf-8",
	)
	# Headless Chrome ignores window sizes below a few hundred pixels: ask for
	# more and crop.  The file URL needs a Windows-style path.
	win_w, win_h = max(width, 500), max(height, 500)
	subprocess.run([
		browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
		f"--user-data-dir={Path(workdir) / 'profile'}",
		"--default-background-color=00000000",
		f"--window-size={win_w},{win_h}",
		f"--screenshot={shot}",
		page.resolve().as_uri(),
	], check=True, capture_output=True)
	return Image.open(shot).convert("RGBA").crop((0, 0, width, height))


def downsample(img, size):
	"""LANCZOS resize with premultiplied alpha (no dark fringes on white lines)."""
	a = np.asarray(img, dtype=np.float32) / 255.0
	pre = a.copy()
	pre[..., :3] *= a[..., 3:4]
	small = Image.fromarray((pre * 255 + 0.5).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
	s = np.asarray(small, dtype=np.float32) / 255.0
	alpha = s[..., 3:4]
	rgb = np.where(alpha > 0, s[..., :3] / np.maximum(alpha, 1e-6), 0)
	out = np.concatenate([rgb, alpha], axis=-1)
	return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def raster(svg_text, w, h, browser, workdir, supersample=4):
	big = render(svg_text, w * supersample, h * supersample, browser, workdir)
	return downsample(big, (w, h))


# ---- outputs ---------------------------------------------------------------

# favicon sizes -> stroke weight (heavier lines survive the small sizes)
ICO_SIZES = [(16, 11), (32, 6.5), (48, 5)]


def main():
	ap = argparse.ArgumentParser(description="Build the Elephant Door mark and favicon set.")
	ap.add_argument("--preview", action="store_true", help="also write tools/icon_preview.png")
	args = ap.parse_args()

	browser = find_browser()
	(ASSETS / "logos").mkdir(parents=True, exist_ok=True)
	written = []

	def save_svg(path, text):
		path.write_text(text, encoding="utf-8")
		written.append(path)

	save_svg(ASSETS / "logos" / "elephant-door-mark.svg", svg(stroke=3))
	save_svg(ASSETS / "favicon.svg", svg(stroke=6, square=True, pad=4))

	with tempfile.TemporaryDirectory() as tmp:
		mark_h = 1024
		mark_w = round(mark_h * W / H)
		mark = raster(svg(stroke=3), mark_w, mark_h, browser, tmp)
		mark.save(ASSETS / "logos" / "elephant-door-mark.png")
		written.append(ASSETS / "logos" / "elephant-door-mark.png")

		icons = [
			raster(svg(stroke=st, square=True, pad=4), px, px, browser, tmp)
			for px, st in ICO_SIZES
		]
		# Pillow skips every size larger than the base image, so the largest goes first.
		icons[-1].save(ASSETS / "favicon.ico", format="ICO",
					   sizes=[(px, px) for px, _ in ICO_SIZES], append_images=icons[:-1])
		written.append(ASSETS / "favicon.ico")

		touch = raster(svg(stroke=4, square=True, pad=12, bg=SITE_BG), 180, 180, browser, tmp)
		touch.convert("RGB").save(ASSETS / "apple-touch-icon.png")
		written.append(ASSETS / "apple-touch-icon.png")

		if args.preview:
			sheet = contact_sheet(mark, icons, touch, browser, tmp)
			sheet.save(ROOT / "tools" / "icon_preview.png")
			written.append(ROOT / "tools" / "icon_preview.png")

	for p in written:
		print(f"wrote {p.relative_to(ROOT)}  ({p.stat().st_size} bytes)")


def contact_sheet(mark, icons, touch, browser, workdir):
	"""Every output on light and dark ground, each with a 4x blow-up, plus favicon.svg at 32 px."""
	light, dark = (240, 240, 240, 255), (32, 33, 36, 255)
	svg_fav = raster(svg(stroke=6, square=True, pad=4), 32, 32, browser, workdir)
	rows = icons + [svg_fav]
	half = (mark.width // 2, mark.height // 2)
	rows_h = sum(r.height * 4 + 32 for r in rows) + touch.height + 40
	sheet = Image.new("RGBA", (half[0] + 700, max(half[1] + 40, rows_h)), (90, 90, 90, 255))
	sheet.alpha_composite(downsample(mark, half), (20, 20))
	x0 = half[0] + 60
	y = 20
	for img in rows:
		for i, ground in enumerate((light, dark)):
			x = x0 + i * 320
			cell = Image.new("RGBA", (img.width + 24, img.height + 24), ground)
			cell.alpha_composite(img, (12, 12))
			sheet.alpha_composite(cell, (x, y))
			big = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
			cellb = Image.new("RGBA", (big.width + 8, big.height + 8), ground)
			cellb.alpha_composite(big, (4, 4))
			sheet.alpha_composite(cellb, (x + img.width + 36, y))
		y += img.height * 4 + 32
	sheet.alpha_composite(touch, (x0, y))
	return sheet


if __name__ == "__main__":
	main()
