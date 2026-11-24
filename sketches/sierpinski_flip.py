import argparse
import math
import os
import numpy as np
from PIL import Image

STOPS = np.array([
    [0, 229, 255],
    [0, 245, 160],
    [255, 209, 102],
    [255, 140, 26],
    [255, 46, 136],
    [123, 97, 255],
    [0, 229, 255],
], dtype=np.float32) / 255.0

BG = np.array([11, 19, 43], dtype=np.float32) / 255.0


def render_carpet(level=5, cell_px=9):
    n = 3 ** level
    yy, xx = np.mgrid[0:n, 0:n]
    alive = np.ones((n, n), dtype=bool)
    tx, ty = xx.copy(), yy.copy()
    for _ in range(level):
        alive &= ~((tx % 3 == 1) & (ty % 3 == 1))
        tx //= 3
        ty //= 3

    u = xx.astype(np.float32) / n
    v = yy.astype(np.float32) / n
    dist = np.sqrt((u - 0.5) ** 2 + (v - 0.5) ** 2) * 1.35
    hue = ((u * 0.42 + v * 0.36 + dist * 0.55) % 1.0) * (len(STOPS) - 1)
    i0 = np.floor(hue).astype(np.int32)
    i1 = np.minimum(len(STOPS) - 1, i0 + 1)
    f = (hue - i0)[:, :, None]
    cols = STOPS[i0] * (1.0 - f) + STOPS[i1] * f

    img_n = n * cell_px
    rgb = np.repeat(np.repeat(cols, cell_px, axis=0), cell_px, axis=1)
    mask = np.repeat(np.repeat(alive, cell_px, axis=0), cell_px, axis=1)

    if cell_px >= 4:
        ly = np.tile(np.arange(cell_px), n)[:, None]
        lx = np.tile(np.arange(cell_px), n)[None, :]
        shade = np.ones((img_n, img_n), dtype=np.float32)
        shade[(ly == 0) | (lx == 0)] = 1.22
        shade[(ly == cell_px - 2) | (lx == cell_px - 2)] = 0.70
        mask &= ~((ly == cell_px - 1) | (lx == cell_px - 1))
        rgb = np.clip(rgb * shade[:, :, None], 0.0, 1.0)

    out = np.where(mask[:, :, None], rgb, BG)
    return Image.fromarray((out * 255.0).astype(np.uint8))


def main():
    p = argparse.ArgumentParser(description="Sierpinski carpet fractal renderer")
    p.add_argument("--level", type=int, default=5)
    p.add_argument("--size", type=int, default=1080)
    p.add_argument("--out", default="sierpinski_flip.png")
    p.add_argument("--gif", action="store_true", help="export a level 1..5 + zoom gif")
    args = p.parse_args()
    level = max(1, min(6, args.level))

    if args.gif:
        sz = min(args.size, 640)
        frames = []
        max_lv = min(level, 5)
        for lv in range(1, max_lv + 1):
            cpx = max(3, int(round(729 / (3 ** lv))))
            im = render_carpet(lv, cell_px=cpx).resize((sz, sz), Image.Resampling.LANCZOS)
            frames.extend([im] * 6)
        hi = render_carpet(max_lv, cell_px=9)
        w = hi.size[0]
        # smooth zoom into fractal interior and back out (zero jump at z=1.0)
        for k in range(24):
            u = 0.5 - 0.5 * math.cos(k / 23.0 * math.tau)
            z = 1.0 + 3.2 * u
            crop = w / z
            half = crop * 0.5
            cx = min(w - half, max(half, w * (0.50 + 0.18 * u)))
            cy = min(w - half, max(half, w * (0.50 + 0.18 * u)))
            box = (cx - half, cy - half, cx + half, cy + half)
            frames.append(hi.crop(box).resize((sz, sz), Image.Resampling.LANCZOS))
        out_gif = os.path.splitext(args.out)[0] + ".gif"
        frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=65, loop=0)
        print(f"saved {out_gif}")
    else:
        cpx = 9 if level == 5 else max(3, int(round(1080 / (3 ** level))))
        im = render_carpet(level, cell_px=cpx).resize((args.size, args.size), Image.Resampling.LANCZOS)
        im.save(args.out)
        print(f"saved {args.out}")


if __name__ == "__main__":
    main()
