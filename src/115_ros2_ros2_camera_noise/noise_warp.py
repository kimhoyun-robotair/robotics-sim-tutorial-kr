"""Equivalent GPU augmentation; normalized sigma=0.1 means 25.5 intensity units."""
import warp as wp


@wp.kernel
def gaussian_noise(data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), seed: int, sigma: float = 0.1):
    row, col = wp.tid()
    pixel = row * data_out.shape[1] + col
    for channel in range(3):
        state = wp.rand_init(seed, pixel + channel * data_out.shape[0] * data_out.shape[1])
        value = float(data_in[row, col, channel]) + 255.0 * sigma * wp.randn(state)
        data_out[row, col, channel] = wp.uint8(wp.clamp(value, 0.0, 255.0))
