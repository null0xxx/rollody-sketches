import argparse
import math
import numpy as np
from PIL import Image, ImageFilter

PETALS = 13
SHELLS = 28
PTS_PER_SHELL = 1800
SIZE = 1080

PALETTE = {
    "bg": np.array([26, 15, 46], dtype=np.float32) / 255.0,
    "orchid": np.array([139, 36, 109], dtype=np.float32) / 255.0,
    "rose": np.array([227, 74, 133], dtype=np.float32) / 255.0,
    "coral": np.array([255, 90, 95], dtype=np.float32) / 255.0,
    "blush": np.array([244, 215, 212], dtype=np.float32) / 255.0,
    "white": np.array([1.0, 0.98, 0.99], dtype=np.float32),
    "ice": np.array([111, 216, 255], dtype=np.float32) / 255.0,
}


def build_lotus(petals=PETALS, shells=SHELLS, pts_per_shell=PTS_PER_SHELL):
    theta = np.linspace(0.0, math.tau, pts_per_shell, endpoint=False, dtype=np.float32)
    xs, ys, zs, cols = [], [], [], []

    for s in range(shells):
        twist = s * 0.046
        if s < 16:
            u = s / 15.0
            scale = 0.24 + 0.44 * (u ** 0.85)
            rose = np.abs(np.sin(petals * 0.5 * theta + twist * 0.45)) ** 0.78
            flare = 0.84 + 0.16 * np.cos(petals * theta + twist * 1.4)
            r = scale * (0.16 + 0.84 * rose) * flare
            ang = theta + twist * 0.92
            z = 0.34 * np.cos(r * math.pi * 1.05) + 0.06 * np.sin(petals * theta)

            mix = np.clip(rose * 0.72 + u * 0.28, 0.0, 1.0)[:, None]
            base = PALETTE["orchid"] * (1.0 - u) + PALETTE["rose"] * u
            col = base * (1.0 - mix) + PALETTE["coral"] * mix
            tip = np.clip((rose - 0.82) / 0.18, 0.0, 1.0)[:, None]
            col = col * (1.0 - tip * 0.52) + PALETTE["blush"] * (tip * 0.52)
            gain = 0.75 + 0.55 * u
        elif s < 24:
            # half-petal offset so outer crown sits between inner petals
            u = (s - 16) / 7.0
            scale = 0.64 + 0.30 * u
            phase = theta + math.pi / petals + twist * 0.35
            crown = (0.5 + 0.5 * np.cos(petals * phase)) ** 0.92
            r = scale * (0.48 + 0.52 * crown) * (0.92 + 0.08 * np.sin(2.0 * petals * phase))
            ang = phase + 0.07 * np.sin(petals * phase) * u
            z = 0.22 * np.cos(r * math.pi) - 0.09 * crown + 0.05 * np.sin(2.0 * petals * phase)

            mix = np.clip(crown * 0.78 + u * 0.35, 0.0, 1.0)[:, None]
            col = PALETTE["rose"] * (1.0 - mix) + PALETTE["blush"] * mix
            spark = np.clip((crown - 0.75) / 0.25, 0.0, 1.0)[:, None]
            col = col * (1.0 - spark * 0.65) + PALETTE["white"] * (spark * 0.65)
            gain = 0.85 + 0.50 * u
        else:
            u = (s - 24) / max(1, shells - 25)
            scale = 0.88 + 0.14 * u
            phase = theta + math.pi / petals + twist * 0.22
            star = (0.5 + 0.5 * np.cos(petals * phase)) ** 1.35
            r = scale * (0.62 + 0.38 * star + 0.06 * np.sin(3.0 * petals * phase + u * 2.0))
            ang = phase + 0.10 * np.sin(petals * phase)
            z = -0.06 + 0.12 * np.cos(petals * phase) - 0.08 * u

            glint = (0.5 + 0.5 * np.sin(theta * 2.0 - 0.6))[:, None] * 0.28
            col = PALETTE["blush"] * (1.0 - 0.55 * star[:, None]) + PALETTE["white"] * (0.55 * star[:, None])
            col = col * (1.0 - glint) + PALETTE["ice"] * glint
            gain = 1.05 + 0.45 * u

        xs.append((r * np.cos(ang)).astype(np.float32))
        ys.append((r * np.sin(ang)).astype(np.float32))
        zs.append(z.astype(np.float32))
        cols.append((col * gain).astype(np.float32))

    return np.concatenate(xs), np.concatenate(ys), np.concatenate(zs), np.concatenate(cols)


def render_frame(px, py, pz, pcol, count, rx, ry, rz, size=SIZE):
    x, y, z, c = px[:count], py[:count], pz[:count], pcol[:count]

    cz, sz = math.cos(rz), math.sin(rz)
    x1, y1 = x * cz - y * sz, x * sz + y * cz

    cx, sx = math.cos(rx), math.sin(rx)
    y2, z2 = y1 * cx - z * sx, y1 * sx + z * cx

    cy, sy = math.cos(ry), math.sin(ry)
    x3, z3 = x1 * cy + z2 * sy, -x1 * sy + z2 * cy

    cam = 3.25
    scale = (size * 0.44) * (cam / (cam - z3))
    ix = (size * 0.5 + x3 * scale).astype(np.int32)
    iy = (size * 0.5 + y2 * scale).astype(np.int32)

    ok = (ix >= 2) & (ix < size - 2) & (iy >= 2) & (iy < size - 2)
    vx, vy, vc = ix[ok], iy[ok], c[ok]

    hdr = np.zeros((size, size, 3), dtype=np.float32)
    np.add.at(hdr, (vy, vx), vc * 0.75)
    np.add.at(hdr, (vy, vx + 1), vc * 0.35)
    np.add.at(hdr, (vy + 1, vx), vc * 0.35)
    np.add.at(hdr, (vy + 1, vx + 1), vc * 0.20)

    # soft optical bloom via pillow gaussian on downscaled buffer
    bloom_img = Image.fromarray(np.clip(hdr * 110.0, 0, 255).astype(np.uint8))
    bloom_small = bloom_img.resize((size // 2, size // 2), Image.Resampling.BILINEAR)
    bloom_small = bloom_small.filter(ImageFilter.GaussianBlur(radius=9))
    bloom = np.asarray(bloom_small.resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0

    # subtle studio vignette + warm/cool edge light
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    bg = np.broadcast_to(PALETTE["bg"], (size, size, 3)).copy()
    dl = np.exp(-((xx + 0.05) ** 2 + (yy - 0.45) ** 2) * 3.8)[:, :, None]
    dr = np.exp(-((xx - 1.05) ** 2 + (yy - 0.45) ** 2) * 3.8)[:, :, None]
    bg += dl * PALETTE["coral"] * 0.16 + dr * PALETTE["ice"] * 0.14

    lit = 1.0 - np.exp(-(hdr * 1.25 + bloom * 0.85))
    out = np.clip(bg + lit, 0.0, 1.0)
    return Image.fromarray((out * 255.0).astype(np.uint8))


def main():
    p = argparse.ArgumentParser(description="3D polar harmonic crystal lotus")
    p.add_argument("--petals", type=int, default=PETALS)
    p.add_argument("--shells", type=int, default=SHELLS)
    p.add_argument("--size", type=int, default=SIZE)
    p.add_argument("--out", default="lotus_bloom.png")
    p.add_argument("--gif", action="store_true", help="export a blooming animation gif")
    args = p.parse_args()

    px, py, pz, pcol = build_lotus(args.petals, args.shells)
    total = len(px)

    if args.gif:
        frames = []
        n = 72
        for i in range(n):
            t = i / (n - 1)
            prog = min(1.0, 0.12 + 0.88 * min(1.0, t / 0.82))
            count = int(total * (1.0 - (1.0 - prog) ** 1.35))
            img = render_frame(
                px, py, pz, pcol, count,
                rx=0.25 * math.sin(t * math.tau * 0.6),
                ry=0.20 * math.cos(t * math.tau * 0.5),
                rz=t * 1.4,
                size=min(args.size, 640),
            )
            frames.append(img)
        out_gif = args.out.rsplit(".", 1)[0] + ".gif"
        frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=50, loop=0)
        print(f"saved {out_gif}")
    else:
        img = render_frame(px, py, pz, pcol, total, rx=0.22, ry=0.16, rz=0.42, size=args.size)
        img.save(args.out)
        print(f"saved {args.out}")


if __name__ == "__main__":
    main()
