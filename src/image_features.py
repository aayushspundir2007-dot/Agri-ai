"""Shared image feature extractor for the Plant Disease module.

Dependency-free (NumPy + Pillow only) so it runs on the same Python used by the
Streamlit app, including Python 3.14 where TensorFlow is unavailable.

The trainer (src/train_disease.py) and the app (app.py) MUST use this exact
function so training and inference features match.
"""
from pathlib import Path
import numpy as np
from PIL import Image

IMG_SIZE = (32, 32)  # thumbnail size used for every feature channel


def extract_features(image):
    """Fixed-length 1-D float32 feature vector (~1120 dims) for a leaf image.

    Accepts a file path, a PIL Image, or an (H,W,3) uint8 array.
    Composition: 32x32 grayscale thumbnail + RGB histograms + RGB stats +
    HSV histograms + grayscale stats.
    """
    if isinstance(image, (str, Path)):
        image = Image.open(image)
    elif isinstance(image, np.ndarray):
        image = Image.fromarray(image.astype("uint8"))
    image = image.convert("RGB").resize(IMG_SIZE)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b

    feats = [gray.reshape(-1)]
    for c in (r, g, b):
        h, _ = np.histogram(c, bins=16, range=(0.0, 1.0))
        feats.append(h / (h.sum() + 1e-6))
    for c in (r, g, b):
        feats.append(np.array([c.mean(), c.std()], dtype=np.float32))

    hsv = np.asarray(image.convert("HSV"), dtype=np.float32)
    for ch, nb in ((0, 16), (1, 16), (2, 8)):
        h, _ = np.histogram(hsv[..., ch], bins=nb, range=(0.0, 255.0))
        feats.append(h / (h.sum() + 1e-6))

    feats.append(np.array([gray.mean(), gray.std()], dtype=np.float32))
    return np.concatenate([np.atleast_1d(np.ravel(f)) for f in feats]).astype(np.float32)


if __name__ == "__main__":
    # quick sanity check: feature length must be deterministic
    from PIL import Image as _I
    import sys
    dummy = _I.new("RGB", (64, 64), (120, 160, 80))
    print("feature_dim", len(extract_features(dummy)))
