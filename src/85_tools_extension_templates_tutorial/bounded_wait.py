def wait_for_target(articulation, indices, target, tolerance=0.001, max_steps=300):
    """Yield between real articulation readings; caller advances once per physics step."""
    import numpy as np
    if max_steps <= 0 or tolerance <= 0:
        raise ValueError("max_steps and tolerance must be positive")
    for _ in range(max_steps):
        actual = articulation.get_joint_positions()[indices]
        if np.allclose(actual, target, atol=tolerance, rtol=0):
            return True
        yield
    raise TimeoutError("Articulation did not reach the target within max_steps")
