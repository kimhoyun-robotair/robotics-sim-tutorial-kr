"""Replicator CPU augmentation: sigma is standard deviation in 8-bit intensity units."""
import numpy as np


def gaussian_noise(data_in: np.ndarray, seed: int, sigma: float = 25.5) -> np.ndarray:
    rgb = data_in[..., :3].astype(np.float32)
    rng = np.random.default_rng(seed)
    return np.clip(rgb + rng.normal(0.0, sigma, rgb.shape), 0, 255).astype(np.uint8)
