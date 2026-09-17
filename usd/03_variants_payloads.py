#!/usr/bin/env python3
"""Variant로 선택지를 기록하고 payload를 필요할 때 불러온다.

실행: python 03_variants_payloads.py --output /tmp/usd-variants-new
의존성: OpenUSD의 pxr. 앞 실습의 파일 없이 독립 실행한다.

출처 — NVIDIA Learn OpenUSD:
https://docs.nvidia.com/learn-openusd/latest/composition-basics/variant-sets.html
https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/variant-sets/working-with-variant-sets.html
https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/references-payloads/what-are-payloads.html
https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/references-payloads/working-with-payloads.html
"""

import argparse
from datetime import datetime
from pathlib import Path


def main() -> int:
    """선택 가능한 자산과 payload 진입점을 저장하고 합성 상태를 출력한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="새 출력 디렉터리. 기본값: outputs/usd/03_variants_payloads/<실행 시각>",
    )
    args = parser.parse_args()
    # --help는 pxr가 없는 일반 Python 환경에서도 동작한다.
    try:
        from pxr import Gf, Usd, UsdGeom
    except ImportError as exc:
        parser.error(f"pxr를 불러올 수 없습니다. usd/README.md의 실행 환경을 확인하세요: {exc}")

    output = args.output or (
        Path(__file__).resolve().parents[1] / "outputs" / "usd"
        / "03_variants_payloads" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output = output.expanduser().resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"출력 경로가 이미 있습니다. 새 디렉터리를 지정하세요: {output}")

    # 1. Variant set은 선택지의 묶음이다. 여기서는 bodySize 안에 small/large가 있다.
    asset_path = output / "variant_asset.usda"
    asset = Usd.Stage.CreateNew(str(asset_path))
    UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(asset, 1.0)
    robot = UsdGeom.Xform.Define(asset, "/Robot")
    asset.SetDefaultPrim(robot.GetPrim())
    variants = robot.GetPrim().GetVariantSets().AddVariantSet("bodySize")

    for name, size, color in (
        ("small", 0.5, Gf.Vec3f(0.2, 0.6, 1.0)),
        ("large", 1.0, Gf.Vec3f(1.0, 0.4, 0.1)),
    ):
        variants.AddVariant(name)
        variants.SetVariantSelection(name)
        # 선택만 바꿔서는 이후 Set()이 variant 내부로 들어가지 않는다.
        # 반드시 edit context 안에서 선택지에 속하는 Prim/속성을 작성한다.
        # 밖에 같은 속성의 local opinion을 쓰면 더 강해서 선택 결과를 가릴 수 있다.
        with variants.GetVariantEditContext():
            body = UsdGeom.Cube.Define(asset, "/Robot/Body")
            body.CreateSizeAttr(size)
            body.CreateDisplayColorAttr([color])
            body.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, size / 2.0))

    # 선택을 바꿀 때마다 같은 /Robot/Body에서 서로 다른 합성 값을 읽는다.
    print("variant 목록:", variants.GetVariantNames())
    for name in ("small", "large"):
        variants.SetVariantSelection(name)
        body = UsdGeom.Cube.Get(asset, "/Robot/Body")
        print(f"variant={name}: size={body.GetSizeAttr().Get()}")
    # 파일에 남길 기본 선택은 small이다. 전체 선택지 정의도 함께 저장된다.
    variants.SetVariantSelection("small")
    asset.GetRootLayer().Save()

    # 2. Payload는 로드/언로드를 제어할 수 있는 합성 연결이다.
    # 실전에서는 무거운 상세 메시 등을 별도 파일에 두지만, 원리만 보이도록
    # 앞에서 만든 작은 자산을 payload로 사용한다. 속도/메모리 벤치마크는 아니다.
    scene_path = output / "payload_scene.usda"
    scene = Usd.Stage.CreateNew(str(scene_path))
    UsdGeom.SetStageUpAxis(scene, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(scene, 1.0)
    world = UsdGeom.Xform.Define(scene, "/World")
    scene.SetDefaultPrim(world.GetPrim())
    unloaded_robot = UsdGeom.Xform.Define(scene, "/World/Robot")
    # 로컬 Prim은 파일에 남고, payload 반대편의 /Robot 및 자식들은 로드 대상이다.
    unloaded_robot.GetPrim().GetPayloads().AddPayload("./variant_asset.usda")
    scene.GetRootLayer().Save()

    # LoadNone은 payload를 제외하고 연다. Reference와 일반 sublayer까지 끄지는 않는다.
    deferred = Usd.Stage.Open(str(scene_path), load=Usd.Stage.LoadNone)
    robot_prim = deferred.GetPrimAtPath("/World/Robot")
    body_path = "/World/Robot/Body"
    print(f"LoadNone: Robot 존재={bool(robot_prim)}, IsLoaded={robot_prim.IsLoaded()}")
    print(f"LoadNone: Body 존재={bool(deferred.GetPrimAtPath(body_path))}")

    # 필요한 Prim 아래의 payload를 명시적으로 로드하면 Body가 합성 결과에 나타난다.
    deferred.Load("/World/Robot")
    print(f"Load 후: IsLoaded={robot_prim.IsLoaded()}")
    loaded_body = UsdGeom.Cube.Get(deferred, body_path)
    print(f"Load 후: Body 존재={bool(loaded_body)}, size={loaded_body.GetSizeAttr().Get()}")

    # 자산의 기본 선택(small)은 유지하면서 이 scene에서만 large를 선택할 수 있다.
    scene_variants = robot_prim.GetVariantSets().GetVariantSet("bodySize")
    scene_variants.SetVariantSelection("large")
    print(f"scene에서 large 선택: size={UsdGeom.Cube.Get(deferred, body_path).GetSizeAttr().Get()}")
    deferred.GetRootLayer().Save()
    print(f"자산에 남은 선택: {variants.GetVariantSelection()}")

    # Unload는 자산 파일이나 선택지를 삭제하지 않는다. 이 Stage의 로딩 상태를 바꾼다.
    # 이 로딩 상태는 USDA에 저장되지 않는다. 다시 Open()하면 기본은 LoadAll이다.
    deferred.Unload("/World/Robot")
    print(f"Unload 후: Body 존재={bool(deferred.GetPrimAtPath(body_path))}")
    print(f"선택지 자산: {asset_path}")
    print(f"payload 진입점: {scene_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
