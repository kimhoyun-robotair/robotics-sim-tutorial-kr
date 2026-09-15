"""Register a recorder-selectable RGB/normal writer inside an already running Kit."""
import numpy as np
from omni.replicator.core import AnnotatorRegistry, BackendDispatch, Writer, WriterRegistry


class BeginnerNormalWriter(Writer):
    def __init__(self, output_dir, rgb=True, normals=True):
        self.version = "1.0"
        self.annotators = []
        self.backend = BackendDispatch({"paths": {"out_dir": output_dir}})
        self.frame = 0
        for name, enabled in [("rgb", rgb), ("normals", normals)]:
            if enabled:
                self.annotators.append(AnnotatorRegistry.get_annotator(name))

    def write(self, data):
        for key, values in data.items():
            if key.startswith("rgb"):
                self.backend.write_image(f"{key}/{self.frame:06d}.png", values)
            elif key.startswith("normals"):
                color = np.clip((values[..., :3] + 1) * 127.5, 0, 255).astype(np.uint8)
                self.backend.write_image(f"{key}/{self.frame:06d}.png", color)
        self.frame += 1


if "BeginnerNormalWriter" not in WriterRegistry.get_writers():
    WriterRegistry.register(BeginnerNormalWriter)
