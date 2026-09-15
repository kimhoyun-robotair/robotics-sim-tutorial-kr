# 46. Jetbot asset의 mesh와 instance 구조 최적화

권장 학습 순서 **46** · 로봇 자산 가져오기와 제작 · 출처 ID `t130`

공식 Asset Optimization 수업의 **GUI native** 실습이다. Isaac Sim 5.1의 `/Isaac/Samples/Rigging/Jetbot/Jetbot_Base/Jetbot_base.usd`를 로컬 편집 layer에 sublayer로 넣고 시작한다. `inspect_meshes.py`는 실제 mesh 수, face 수, instance proxy, prototype을 출력하므로 변경 전후 구조를 비교할 수 있다. FPS 향상 수치는 이 패키지에서 측정하지 않았다.

## 준비와 실행

Isaac Sim **5.1.0**, RTX GPU와 GUI, 위 Jetbot asset에 접근할 수 있는 assets root, Mesh Merge Tool이 필요하다. **Prim**은 장면 노드, **Mesh**는 렌더링 기하, **Rigid body/link**는 같이 움직이는 물리 묶음, **reference**는 USD 구성을 재사용하는 연결이다. 다른 로컬 튜토리얼을 먼저 읽을 필요가 없다.

```bash
cd src/46_robot_setup_optimizing_asset
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

출발 stage `output/first/stage.usda`에만 편집하고 Ctrl+S로 저장한다. 기본 창은 닫을 때까지 유지된다. 이후 `--stage "$PWD/output/first/stage.usda" --output output/reopen`으로 새 override layer에서 계속할 수 있다.

## 단계별 최적화

1. **Edit → Preferences → Stage → Authoring → Inherit Parent Transform**을 체크한다. Layers의 local root가 authoring layer인지 확인한다. Script Editor에서 `inspect_meshes.py`를 실행해 출력 값을 복사해 둔다.
2. Stage 메뉴 **Show Root**를 켜고 root 바로 아래 Xform `Jetbot_Sim`을 만든다. 우클릭 **Set as Default Prim**. root 바로 아래에는 별도 Scope `Visuals`도 만든다. Default Prim은 다른 파일이 이 asset 전체를 reference할 때 기본 진입점을 정한다.
3. 기존 Jetbot의 링크 prim을 Jetbot_Sim으로 reparent하여 물리·joint 구조를 준비한다. source layer의 원래 prim이 deactivate되면 source 쪽에서 Activate하고, 새 Jetbot_Sim 링크의 시각 geometry 자식만 정리한다. body0/body1 target이 새 링크를 가리키는지 확인하고 물리 API와 joint를 실수로 지우지 않는다.
4. **Tools → Robotics → Asset Editors → Mesh Merge Tool**을 연다. 원본 `Jetbot/left_wheel`을 선택하고 **Combine Materials** 체크, material destination=`/Jetbot_Sim/Looks`, Merge. 서로 다른 rigid link를 한 mesh로 합치지 않는다.
5. 결과 `/Merged/left_wheel`의 transform을 검사한다. mesh의 좌표를 어느 frame 기준으로 bake했는지 확인하고 중복 transform이 적용되지 않도록 정리한다. `/Visuals/left_wheel` Xform 아래로 결과 mesh를 이동하고 불필요한 Merged parent를 제거한다.
6. `/Jetbot_Sim/left_wheel/Visuals` Xform을 만들고 **Add → Reference**. 임시 파일 선택 후 Property → References의 **Asset Path는 비우고**, **Prim Path=/Visuals/left_wheel**로 설정한다. 이것은 같은 stage 안의 원본 visual을 참조하는 **internal reference**다. reference를 `/Visuals/left_wheel` 자기 자신에 걸면 cycle이므로 대상과 인스턴스 위치를 구분한다.
7. source visual 자료용 `/Visuals`는 숨겨 원점의 원본 mesh가 표시되지 않게 한다. 다른 링크에도 같은 방식으로 합치고 reference한다. 완성 중간 비교 asset은 `/Isaac/Samples/Rigging/Jetbot/Jetbot_Optimized/Jetbot_optimized_post_merge.usd`다.
8. 좌우 바퀴 기하가 같다면 `/Visuals/left_wheel`을 `/Visuals/wheel`로 rename한다. 왼쪽·오른쪽 `/Jetbot_Sim/.../Visuals`의 reference Prim Path를 모두 `/Visuals/wheel`로 바꾼다. 오른쪽 원본 visual은 더 이상 참조되지 않을 때 제거한다.
9. `/Jetbot_Sim` 아래 각 referenced `Visuals` prim의 **Instanceable**을 체크한다. 파란 I 표시와 prototype 생성 여부를 확인한다. `inspect_meshes.py`를 다시 실행해 instance roots/prototypes와 mesh occurrences를 비교한다.
10. 동일한 camera, 해상도, 조명, 로봇 수, physics step으로 Play해서 표시·collision·joint 동작이 유지되는지 확인한다. 단순 prim 감소가 실제 성능 향상을 증명하지는 않으므로 renderer/physics profiler로 병목도 확인한다. 최종 비교 asset은 `Jetbot_optimized_final.usd`다.

## 해설과 관찰 기준

Mesh merge는 한 링크 안의 draw/scenegraph 관리 비용을 줄이는 작업이다. material binding을 잃거나 collider를 visual과 함께 합치면 외관·물리가 달라질 수 있다. scenegraph instancing은 동일한 reference subgraph를 공유해 메모리를 줄이는 방식이다. **reference만 있다고 instance가 되는 것은 아니며**, Instanceable을 지정해야 한다. instance proxy 자식은 개별 속성을 수정할 수 없으므로 개별 색/기하가 필요한 부품은 공유 경계를 다시 설계한다.

검사 스크립트는 `Usd.PrimRange.Stage(..., Usd.TraverseInstanceProxies())`로 표시되는 mesh occurrence도 세고 `GetPrototypes()`로 실제 prototype 수를 읽는다. instance 때문에 일반 Traverse의 mesh 수가 줄어든 것을 mesh가 사라진 것으로 오판하지 않는다.

한 변수 실험은 같은 merged stage에서 **Instanceable만** 켰다/껐다 비교하는 것이다. mesh merge까지 동시에 바꾸지 않는다. 추가로 조명 수·반투명 재질·과도한 collider contact를 줄일 수 있지만 각 변경은 품질과 물리 정밀도 tradeoff가 있다. wheel collider는 매끈한 cylinder/sphere 근사가 바퀴 mesh를 그대로 쓰는 것보다 안정적으로 굴러갈 수 있다.

mesh가 사라지면 internal reference 경로·active/visibility·instance proxy를 확인한다. 위치가 변하면 reparent 이전/이후 world transform과 merge transform bake를 확인한다. 검증 범위: 문법·CLI·asset URL 접근. 실제 mesh merge, 물리 보존 및 성능 개선은 미검증이다.

## 출처

- [Isaac Sim 5.1 Asset Optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html)
- [Mesh merge](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html#merge-meshes), [Scenegraph instancing](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html#scenegraph-instancing)
