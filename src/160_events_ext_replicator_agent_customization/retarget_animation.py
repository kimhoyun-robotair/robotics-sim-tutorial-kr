"""Script Editor helper for native NVIDIA animation retargeting."""
import omni.kit.commands
import omni.usd
from pxr import UsdSkel


def retarget_animation(source_skeleton, target_skeleton, source_animation, output_parent):
    stage = omni.usd.get_context().get_stage()
    for path in (source_skeleton, target_skeleton):
        if not stage.GetPrimAtPath(path).IsA(UsdSkel.Skeleton):
            raise ValueError(f"Expected Skeleton prim: {path}")
    if not stage.GetPrimAtPath(source_animation).IsA(UsdSkel.Animation):
        raise ValueError("Source animation must be a SkelAnimation prim")
    if stage.GetPrimAtPath(output_parent):
        raise ValueError("Choose an unused output parent to preserve existing animations")
    return omni.kit.commands.execute(
        "CreateRetargetAnimationsCommand",
        source_skeleton_path=source_skeleton,
        target_skeleton_path=target_skeleton,
        source_animation_paths=[source_animation],
        target_animation_parent_path=output_parent,
        set_root_identity=False,
    )
