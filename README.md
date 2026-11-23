# rollody-sketches

Standalone Python sketches for the math and generative art animations on [@RollodyStudio](https://www.youtube.com/@RollodyStudio).

Each sketch is a single self-contained file using only `numpy` and `pillow` so it runs cleanly on Windows, macOS, and Linux without C-extension setup.

<p align="center">
  <img src="assets/lotus_preview.jpg" width="460" alt="3D Polar Harmonic Crystal Lotus">
</p>

## Setup

```bash
pip install -r requirements.txt
```

## Sketches

| Sketch | File | Video | Command |
|---|---|---|---|
| 3D Polar Harmonic Lotus | `sketches/lotus_bloom.py` | [Watch Short](https://youtube.com/shorts/7ZJ0sNEhubY) | `python sketches/lotus_bloom.py` |

### Options (`lotus_bloom.py`)

```bash
# Default 13-petal 1080x1080 PNG
python sketches/lotus_bloom.py

# Try different petal counts or shell depth
python sketches/lotus_bloom.py --petals 21 --shells 30 --out lotus_21.png

# Export a blooming animation GIF
python sketches/lotus_bloom.py --gif
```

## License

MIT
