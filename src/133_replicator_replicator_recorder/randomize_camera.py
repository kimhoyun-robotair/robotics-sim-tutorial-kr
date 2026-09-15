"""Run inside Script Editor after loading the local recorder scene."""
import omni.replicator.core as rep
camera = rep.create.camera(name="RandomRecorderCamera")
with rep.trigger.on_frame():
    with camera:
        rep.modify.pose(position=rep.distribution.uniform((-3, -5, 2), (3, -3, 4)), look_at="/World/Carton")
print(camera.get_output_prims())
