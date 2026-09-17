#!/usr/bin/env python3
"""자산 재사용과 별도 layer에 기록하는 비파괴 편집을 비교한다.

실행: python 02_layers_references.py --output /tmp/usd-layers-new
의존성: OpenUSD의 pxr. 앞 실습의 파일 없이 독립 실행한다.

출처 — NVIDIA Learn OpenUSD:
https://docs.nvidia.com/learn-openusd/latest/composition-basics/layers.html
https://docs.nvidia.com/learn-openusd/latest/composition-basics/references.html
https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/sublayers/working-with-sublayers.html
"""

import argparse
from datetime import datetime
from pathlib import Path


def main() -> int:
    """자산·배치·수정·진입점·flatten 결과를 각각 USDA로 저장한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="새 출력 디렉터리. 기본값: outputs/usd/02_layers_references/<실행 시각>",
    )
    args = parser.parse_args()
    # 도움말은 일반 Python에서도 확인할 수 있도록 USD import를 뒤로 미룬다.
    try:
        from pxr import Gf, Sdf, Usd, UsdGeom
    except ImportError as exc:
        parser.error(f"pxr를 불러올 수 없습니다. usd/README.md의 실행 환경을 확인하세요: {exc}")

    output = args.output or (
        Path(__file__).resolve().parents[1] / "outputs" / "usd"
        / "02_layers_references" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output = output.expanduser().resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"출력 경로가 이미 있습니다. 새 디렉터리를 지정하세요: {output}")

    # 1. 독립 자산: /Asset이 진입점이고 Geometry가 실제 모양이다.
    asset_path = output / "cube_asset.usda"
    asset = Usd.Stage.CreateNew(str(asset_path))
    UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(asset, 1.0)
    asset_root = UsdGeom.Xform.Define(asset, "/Asset")
    asset.SetDefaultPrim(asset_root.GetPrim())
    asset_cube = UsdGeom.Cube.Define(asset, "/Asset/Geometry")
    asset_cube.CreateSizeAttr(1.0)
    asset_cube.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.6, 1.0)])
    asset.GetRootLayer().Save()
    source_before = asset_path.read_bytes()

    # 2. 배치 layer: 같은 파일을 서로 다른 두 Prim에 reference한다.
    # Reference는 자산 내용을 새 경로에 합성한다. 원본 파일을 복사하지 않는다.
    # 기본 Prim /Asset 자체가 /World/Left 또는 /World/Right에 대응하므로
    # 자식 경로는 /World/Left/Geometry와 /World/Right/Geometry가 된다.
    layout = Usd.Stage.CreateNew(str(output / "layout.usda"))
    UsdGeom.SetStageUpAxis(layout, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(layout, 1.0)
    world = UsdGeom.Xform.Define(layout, "/World")
    layout.SetDefaultPrim(world.GetPrim())
    for name, x_position in (("Left", -1.5), ("Right", 1.5)):
        placement = UsdGeom.Xform.Define(layout, f"/World/{name}")
        # 상대 asset path의 기준은 이 reference를 기록한 layout.usda의 위치다.
        # primPath를 생략했으므로 cube_asset.usda의 defaultPrim을 사용한다.
        placement.GetPrim().GetReferences().AddReference("./cube_asset.usda")
        placement.AddTranslateOp().Set(Gf.Vec3d(x_position, 0.0, 0.5))
    # 배치에만 1.5라는 opinion(작성된 값)을 추가한다. 원본 size=1.0은 유지된다.
    UsdGeom.Cube.Get(layout, "/World/Right/Geometry").GetSizeAttr().Set(1.5)
    layout.GetRootLayer().Save()

    # 3. scene.usda는 진입점이다. Sublayer는 경로를 옮기지 않고 같은 계층에 합성한다.
    # 같은 layer stack에서는 root가 sublayer보다 강하고, 목록 앞쪽이 더 강하다.
    # 따라서 여기서는 overrides > layout 순서다. root에는 size를 작성하지 않는다.
    overrides = Sdf.Layer.CreateNew(str(output / "overrides.usda"))
    scene_path = output / "scene.usda"
    scene = Usd.Stage.CreateNew(str(scene_path))
    scene.GetRootLayer().subLayerPaths = ["./overrides.usda", "./layout.usda"]
    UsdGeom.SetStageUpAxis(scene, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(scene, 1.0)
    scene.SetDefaultPrim(scene.GetPrimAtPath("/World"))

    # Stage에서 읽는 것은 합성 결과다. 쓰는 위치는 edit target으로 결정한다.
    # with 안에서는 overrides.usda에만 기록하고, 나오면 이전 target으로 돌아간다.
    # over는 기존 Prim을 보완할 기록이며, 자산의 형상 정의는 reference에서 가져온다.
    with Usd.EditContext(scene, overrides):
        right_override = scene.OverridePrim("/World/Right/Geometry")
        UsdGeom.Cube(right_override).GetSizeAttr().Set(2.0)
    print(f"현재 edit target: {Path(scene.GetEditTarget().GetLayer().identifier).name}")

    # root.Save()는 root 하나만 저장한다. 수정 layer도 명시적으로 저장해야 한다.
    # scene.Save()를 쓰면 stage에 기여하는 수정된 파일 layer들을 함께 저장한다.
    overrides.Save()
    scene.GetRootLayer().Save()

    # 저장한 진입점을 열면 asset=1.0, layout=1.5, overrides=2.0 중 최종 값을 읽는다.
    reopened = Usd.Stage.Open(str(scene_path))
    for name in ("Left", "Right"):
        cube = UsdGeom.Cube.Get(reopened, f"/World/{name}/Geometry")
        print(f"{name} 최종 size: {cube.GetSizeAttr().Get()}")
    print(f"layout의 Right size: {UsdGeom.Cube.Get(layout, '/World/Right/Geometry').GetSizeAttr().Get()}")
    print(f"원본 asset size: {asset_cube.GetSizeAttr().Get()}")
    print(f"원본 파일 내용 유지: {source_before == asset_path.read_bytes()}")
    print("sublayer 순서:", list(reopened.GetRootLayer().subLayerPaths))

    # Flatten은 합성된 결과를 한 layer로 굽는다. 원래 reference/sublayer 편집 구조와
    # 달라지므로 여기서는 별도 파일로 내보낸다. Save()가 자동 flatten하는 것은 아니다.
    # 외부 텍스처/메시 파일을 묶는 패키징 명령도 아니다.
    flattened_path = output / "flattened.usda"
    reopened.Flatten().Export(str(flattened_path))
    print(f"편집용 진입점: {scene_path}")
    print(f"합성 결과 사본: {flattened_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
