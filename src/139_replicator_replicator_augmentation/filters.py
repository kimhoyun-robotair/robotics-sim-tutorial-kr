"""Local augmentation functions; loaded only after SimulationApp starts."""
import numpy as np
import warp as wp


def swap_red_blue(data_in):
    result = data_in.copy()
    result[..., 0], result[..., 2] = data_in[..., 2], data_in[..., 0]
    return result


def depth_noise(data_in, sigma: float, seed: int):
    noise = np.random.default_rng(seed).normal(0, sigma, data_in.shape)
    return np.maximum(data_in + noise, 0).astype(data_in.dtype)


def channel_noise(data_in, sigma: float, seed: int):
    result = data_in.astype(np.float32)
    result[..., :3] += np.random.default_rng(seed).normal(0, sigma, result[..., :3].shape)
    return np.clip(result, 0, 255).astype(data_in.dtype)


@wp.kernel
def swap_red_blue_gpu(data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8)):
    row, col = wp.tid()
    for channel in range(4):
        source = channel
        if channel == 0:
            source = 2
        elif channel == 2:
            source = 0
        data_out[row, col, channel] = data_in[row, col, source]


@wp.kernel
def depth_noise_gpu(data_in: wp.array2d(dtype=wp.float32), data_out: wp.array2d(dtype=wp.float32), sigma: float, seed: int):
    row, col = wp.tid()
    state = wp.rand_init(seed, row * data_in.shape[1] + col)
    data_out[row, col] = wp.max(0.0, data_in[row, col] + sigma * wp.randn(state))


@wp.kernel
def channel_noise_gpu(data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), sigma: float, seed: int):
    row, col = wp.tid()
    for channel in range(3):
        state = wp.rand_init(seed, (row * data_in.shape[1] + col) * 3 + channel)
        value = float(data_in[row, col, channel]) + sigma * wp.randn(state)
        data_out[row, col, channel] = wp.uint8(wp.clamp(value, 0.0, 255.0))
    data_out[row, col, 3] = data_in[row, col, 3]
