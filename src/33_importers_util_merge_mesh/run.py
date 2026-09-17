"""Merge two authored meshes with distinct materials through the native merge command."""
import argparse
import json
import traceback
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clear-transform', action='store_true')
    parser.add_argument('--keep-sources', action='store_true')
    parser.add_argument('--prepare-only', action='store_true', help='Leave the source meshes for the GUI exercise')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=240, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Use a new output directory and a finite headless frame limit')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from pxr import Gf, Sdf, UsdGeom, UsdShade
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        if not enable_extension('isaacsim.util.merge_mesh'):
            raise RuntimeError('Could not enable isaacsim.util.merge_mesh')
        from isaacsim.util.merge_mesh.commands import MergeMeshesCommand
        # MergeMeshesCommand는 여러 메시를 병합하는 Kit 명령이다.
        omni.kit.commands.register(MergeMeshesCommand)
        stage = omni.usd.get_context().get_stage()
        points = [(-.1,-.1,-.1),(.1,-.1,-.1),(.1,.1,-.1),(-.1,.1,-.1),(-.1,-.1,.1),(.1,-.1,.1),(.1,.1,.1),(-.1,.1,.1)]
        faces = [0,3,2,1, 4,5,6,7, 0,1,5,4, 1,2,6,5, 2,3,7,6, 3,0,4,7]
        paths = []
        for i, color in enumerate(((.8,.1,.1),(.1,.2,.8))):
            # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
            source = UsdGeom.Xform.Define(stage, f'/World/Source_{i}')
            source.AddTranslateOp().Set(Gf.Vec3d(1+i*.3, 0, .2))
            mesh = UsdGeom.Mesh.Define(stage, f'/World/Source_{i}/Geometry')
            mesh.CreatePointsAttr(points)
            mesh.CreateFaceVertexCountsAttr([4]*6)
            mesh.CreateFaceVertexIndicesAttr(faces)
            mesh.CreateSubdivisionSchemeAttr('none')
            material = UsdShade.Material.Define(stage, f'/World/Looks/Material_{i}')
            shader = UsdShade.Shader.Define(stage, f'/World/Looks/Material_{i}/Shader')
            shader.CreateIdAttr('UsdPreviewSurface')
            shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
            # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
            paths.append(str(source.GetPath()))
        omni.usd.get_context().get_selection().set_selected_prim_paths(paths, True)
        if not args.prepare_only:
            ok, merged_path = omni.kit.commands.execute(
                'isaacsim.util.merge_mesh.commands.MergeMeshes', source=paths, clear_transform=args.clear_transform,
                deactivate_source=not args.keep_sources, combine_materials=True, materials_destination='/World/MergedLooks',
            )
            if not ok:
                raise RuntimeError('Native mesh merge failed')
            merged = UsdGeom.Mesh(stage.GetPrimAtPath(merged_path))
            if not merged:
                raise RuntimeError('The merge command did not produce a Mesh prim')
            report = {'merged_path': merged_path, 'faces': len(merged.GetFaceVertexCountsAttr().Get()),
                      'subsets': len(UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(merged.GetPrim()))),
                      'sources_active': [stage.GetPrimAtPath(p).IsActive() for p in paths]}
            if report['faces'] != 12 or report['subsets'] != 2:
                raise RuntimeError(f'Merged topology/material partition mismatch: {report}')
            if report['sources_active'] != [args.keep_sources] * len(paths):
                raise RuntimeError(f'Source activation state mismatch: {report}')
            (args.output / 'report.json').write_text(json.dumps(report, indent=2))
            print(report)
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(args.output / 'scene.usda'))
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            count += 1
    except Exception:
        traceback.print_exc()
        raise
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
