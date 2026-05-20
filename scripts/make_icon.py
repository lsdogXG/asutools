"""asuTools icon: Stardew/Terraria-style pixel-art black dog head.

Generates the dog grid programmatically:
- floppy-ish triangular ears, rounded square head, narrower snout
- 5×5 yellow eyes with + black cross pupils
- pink nose, auto-outlined silhouette
"""
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "asutools" / "resources"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 1024
RADIUS = int(SIZE * 0.225)
GRID_N = 26  # bigger grid → more pixel detail

PALETTE = {
    "#": (10, 10, 12, 255),      # main fur
    "O": (0, 0, 0, 255),         # outline
    "Y": (255, 198, 35, 255),    # Stardew-yellow iris
    "B": (8, 8, 10, 255),        # pupil (cross)
    "N": (52, 52, 56, 255),      # gray-black nose
}

BG_TOP = (250, 246, 235, 255)
BG_BOT = (228, 220, 200, 255)


def make_dog_grid(n: int) -> list[str]:
    g = [["."] * n for _ in range(n)]

    def fill(x0, y0, x1, y1, ch):
        for y in range(max(0, y0), min(n, y1 + 1)):
            for x in range(max(0, x0), min(n, x1 + 1)):
                g[y][x] = ch

    # Layout proportions (scale-friendly):
    cx = n // 2
    # Head body
    head_x0, head_x1 = 3, n - 4
    head_y0, head_y1 = 5, n - 9
    fill(head_x0, head_y0, head_x1, head_y1, "#")

    # Triangular ears (taper from full-base at head top → 1-pixel tip at top of grid)
    ear_h = 5
    ear_w = 5
    left_ear_x = head_x0 + 1            # cols inside head edge
    right_ear_x = head_x1 - ear_w       # right ear base position
    for i in range(ear_h):
        # As we go up (i=0 at head, i=ear_h-1 at tip), taper inward 1 px per step from both sides
        y = head_y0 - 1 - i
        if y < 0:
            break
        inset = i // 2
        l0 = left_ear_x + inset
        l1 = left_ear_x + ear_w - 1 - inset
        r0 = right_ear_x + inset
        r1 = right_ear_x + ear_w - 1 - inset
        # Outer ear fur
        for x in range(l0, l1 + 1):
            g[y][x] = "#"
        for x in range(r0, r1 + 1):
            g[y][x] = "#"
        # Inner ear gray — 1px black rim, gray center; skip very top (tip) and base
        if 1 <= i <= ear_h - 2 and (l1 - l0) >= 2:
            for x in range(l0 + 1, l1):
                g[y][x] = "N"
            for x in range(r0 + 1, r1):
                g[y][x] = "N"

    # Snout: narrower box hanging below head, centered
    snout_x0 = cx - 6
    snout_x1 = cx + 5
    snout_y0 = head_y1 + 1
    snout_y1 = n - 3
    fill(snout_x0, snout_y0, snout_x1, snout_y1, "#")
    # Round the chin a bit
    fill(snout_x0, snout_y1, snout_x0 + 1, snout_y1, ".")
    fill(snout_x1 - 1, snout_y1, snout_x1, snout_y1, ".")

    # Eyes: two 5×5 yellow blocks with + black pupil
    eye_y0 = head_y0 + 3
    for ex0 in (head_x0 + 2, head_x1 - 6):
        fill(ex0, eye_y0, ex0 + 4, eye_y0 + 4, "Y")
        # + cross (5 black pixels)
        cy, cxe = eye_y0 + 2, ex0 + 2
        g[cy - 1][cxe] = "B"
        g[cy][cxe - 1] = "B"
        g[cy][cxe] = "B"
        g[cy][cxe + 1] = "B"
        g[cy + 1][cxe] = "B"

    # Pink nose: centered on snout
    nose_y0 = snout_y0 + 1
    nose_y1 = snout_y0 + 2
    nose_x0 = cx - 2
    nose_x1 = cx + 1
    fill(nose_x0, nose_y0, nose_x1, nose_y1, "N")

    # Mouth: small horizontal slit below nose
    mouth_y = nose_y1 + 2
    if mouth_y < snout_y1:
        fill(cx - 2, mouth_y, cx + 1, mouth_y, "O")

    # Auto outline: any '.' that touches '#' or 'Y' becomes 'O' (4-connected only)
    body_chars = {"#", "Y"}
    out = [row[:] for row in g]
    for y in range(n):
        for x in range(n):
            if g[y][x] != ".":
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < n and 0 <= nx < n and g[ny][nx] in body_chars:
                    out[y][x] = "O"
                    break

    return ["".join(row) for row in out]


def vertical_gradient(w, h, top, bot):
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        gr = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, gr, b, 255)
    return img


def rounded_mask(w, h, radius):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    return m


def render_grid(canvas_size, grid):
    rows = len(grid)
    cols = max(len(r) for r in grid)
    side = max(rows, cols)
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    px = img.load()
    y_off = (side - rows) // 2
    x_off = (side - cols) // 2
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in PALETTE:
                px[x + x_off, y + y_off] = PALETTE[ch]
    return img.resize((canvas_size, canvas_size), Image.Resampling.NEAREST)


def build_master():
    bg = vertical_gradient(SIZE, SIZE, BG_TOP, BG_BOT)
    grid = make_dog_grid(GRID_N)
    dog = render_grid(int(SIZE * 0.86), grid)
    bg.paste(dog, ((SIZE - dog.width) // 2, (SIZE - dog.height) // 2), dog)

    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    lw = max(3, int(SIZE * 0.004))
    ImageDraw.Draw(hl).rounded_rectangle(
        (lw // 2, lw // 2, SIZE - lw // 2, SIZE - lw // 2),
        radius=RADIUS - 1, outline=(0, 0, 0, 28), width=lw,
    )
    bg = Image.alpha_composite(bg, hl)

    mask = rounded_mask(SIZE, SIZE, RADIUS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


def export_icns(master):
    iconset = ROOT / "build" / "asutools.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)
    sizes = [
        (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
    ]
    for s, name in sizes:
        resample = Image.Resampling.NEAREST if s <= 64 else Image.Resampling.LANCZOS
        master.resize((s, s), resample).save(iconset / name, "PNG")
    res = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(OUT_DIR / "icon.icns")],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print("iconutil failed:", res.stderr)
    else:
        print(f"wrote {OUT_DIR / 'icon.icns'}")


def main():
    master = build_master()
    master.save(OUT_DIR / "icon.png", "PNG")
    print(f"wrote {OUT_DIR / 'icon.png'}")
    # Print grid for debugging
    print("\nDog grid:")
    for row in make_dog_grid(GRID_N):
        print(" ", row)
    export_icns(master)


if __name__ == "__main__":
    main()
