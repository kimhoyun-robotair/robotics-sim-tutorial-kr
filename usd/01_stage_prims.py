#!/usr/bin/env python3
"""Stage·Prim·속성·좌표를 만들고, 저장한 USD를 다시 읽는 첫 실습.

실행: python 01_stage_prims.py --output /tmp/usd-stage-new
의존성: OpenUSD의 pxr. Isaac Sim 앱이나 GPU는 사용하지 않는다.

출처 — NVIDIA Learn OpenUSD:
https://docs.nvidia.com/learn-openusd/latest/stage-setting/stage.html
https://docs.nvidia.com/learn-openusd/latest/stage-setting/prims.html
https://docs.nvidia.com/learn-openusd/latest/stage-setting/properties/relationships.html
https://docs.nvidia.com/learn-openusd/latest/scene-description-blueprints/xform.html
https://docs.nvidia.com/learn-openusd/latest/stage-setting/timecodes-timesamples.html
"""

import argparse
from datetime import datetime
from pathlib import Path


def main() -> int:
    """새 출력 디렉터리에 stage.usda를 만들고 핵심 값을 출력한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="새 출력 디렉터리. 기본값: outputs/usd/01_stage_prims/<실행 시각>",
    )
    args = parser.parse_args()

    # --help만 볼 때는 pxr 설치도, Isaac Sim 시작도 필요하지 않다.
    try:
        from pxr import Gf, Sdf, Usd, UsdGeom
    except ImportError as exc:
        parser.error(f"pxr를 불러올 수 없습니다. usd/README.md의 실행 환경을 확인하세요: {exc}")

    # 결과를 덮어쓰지 않는다. 부모 폴더는 만들되 최종 출력 폴더는 새것이어야 한다.
    output = args.output or (
        Path(__file__).resolve().parents[1] / "outputs" / "usd"
        / "01_stage_prims" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output = output.expanduser().resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f"출력 경로가 이미 있습니다. 새 디렉터리를 지정하세요: {output}")

    # Stage는 메모리에서 조회하는 합성된 장면이고, root layer가 저장 파일이다.
    # .usda는 텍스트 형식이므로 실행 후 편집기로 열어도 구조를 읽을 수 있다.
    stage_path = output / "stage.usda"
    stage = Usd.Stage.CreateNew(str(stage_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    # 위 메타데이터는 '1 단위 = 1 m, 위쪽 = Z'라는 약속이다.
    # 기존 숫자나 다른 자산의 좌표를 자동으로 변환하는 명령은 아니다.

    # Prim 경로는 파일 경로가 아니다. /World 아래에 Frame과 Cube를 배치한다.
    world = UsdGeom.Xform.Define(stage, "/World")
    frame = UsdGeom.Xform.Define(stage, "/World/Frame")
    cube = UsdGeom.Cube.Define(stage, "/World/Frame/Cube")
    # defaultPrim은 외부에서 Prim 경로를 생략하고 참조할 때 사용할 진입점이다.
    # 루트 수준 Prim을 지정하며, /World라는 이름 자체는 USD의 필수 규칙이 아니다.
    stage.SetDefaultPrim(world.GetPrim())

    # Cube라는 typed schema가 제공하는 size와 displayColor 속성을 설정한다.
    # size는 변환 전 한 변의 길이이다. displayColor는 정식 재질 연결과 다르다.
    cube.CreateSizeAttr(0.5)
    cube.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.6, 1.0)])
    cube_prim = cube.GetPrim()

    # Attribute는 타입이 있는 값이다. ':'로 의미별 이름 공간을 묶을 수 있다.
    label = cube_prim.CreateAttribute(
        "tutorial:label", Sdf.ValueTypeNames.String, custom=True
    )
    label.Set("학습용 큐브")
    # Relationship은 값 대신 다른 Prim/Property로 향하는 경로들을 보관한다.
    # 여기서는 예제 연결일 뿐, 물리 joint나 부모·자식 관계를 만들지는 않는다.
    world.GetPrim().CreateRelationship("tutorial:focus", custom=True).SetTargets(
        [cube_prim.GetPath()]
    )

    # 자식의 local 좌표에 부모 변환을 합성하면 world 좌표가 된다.
    # 이 예제는 이동만 사용한다. 회전/스케일까지 있으면 단순 덧셈으로 계산할 수 없다.
    frame.AddTranslateOp().Set(Gf.Vec3d(1.0, 0.0, 0.0))
    translate = cube.AddTranslateOp()
    translate.Set(Gf.Vec3d(0.25, 0.0, 0.25))

    # USD는 시간별 값을 기록한다. 다음 코드는 시뮬레이션을 실행하지 않는다.
    # 24 time codes가 1초가 되도록 지정하고, 0과 24에 위치 샘플을 작성한다.
    # Default 값은 t=0 샘플과 별개이며, 시간 인자 없는 Get()에서 조회한다.
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(24)
    stage.SetTimeCodesPerSecond(24)
    translate.Set(Gf.Vec3d(0.0, 0.0, 0.25), Usd.TimeCode(0))
    translate.Set(Gf.Vec3d(1.0, 0.0, 0.25), Usd.TimeCode(24))
    # 지원되는 숫자 타입의 중간 샘플은 기본 선형 보간으로 계산된다.
    # 특정 샘플 삭제: translate.GetAttr().ClearAtTime(Usd.TimeCode(24))
    # 삭제는 현재 edit target에 기록한 값에 적용된다.

    # root layer 하나의 내용을 저장한다. 다른 layer가 생기면 각각 저장해야 한다.
    stage.GetRootLayer().Save()
    reopened = Usd.Stage.Open(str(stage_path))
    saved_cube = UsdGeom.Cube.Get(reopened, "/World/Frame/Cube")
    print(f"파일: {stage_path}")
    print(f"defaultPrim: {reopened.GetDefaultPrim().GetPath()}")
    print(f"size: {saved_cube.GetSizeAttr().Get()} m")
    print(f"사용자 속성: {saved_cube.GetPrim().GetAttribute('tutorial:label').Get()}")
    targets = reopened.GetPrimAtPath("/World").GetRelationship("tutorial:focus")
    print(f"relationship: {[str(path) for path in targets.GetTargets()]}")

    # XformCache는 부모 변환까지 계산한다. 장면을 편집한 뒤 재사용할 때는 Clear한다.
    for time in (Usd.TimeCode.Default(), Usd.TimeCode(12)):
        local = saved_cube.GetLocalTransformation(time).ExtractTranslation()
        cache = UsdGeom.XformCache(time)
        world_position = cache.GetLocalToWorldTransform(saved_cube.GetPrim()).ExtractTranslation()
        print(f"time={time}: local={tuple(local)}, world={tuple(world_position)}")

    # Traverse는 기본 조건에 맞는 활성/정의/로드된 Prim들을 깊이 우선으로 순회한다.
    # 최상단 pseudo-root('/')는 일반 Prim이 아니며 이 순회 결과에는 포함되지 않는다.
    print("Prim 계층:")
    for prim in reopened.Traverse():
        print(f"  {prim.GetPath()} : {prim.GetTypeName()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
