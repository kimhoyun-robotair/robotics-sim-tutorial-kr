# Python Environment
> **출처**: [해당 링크](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)  
  
## Details: How `python.sh` works
> Note!  
> 윈도우면 `python.bat`을 사용하시오  
> `python.bat` 작동이나 `python.sh` 작동이나 매우 유사함   
  
이 `python.sh`는 먼저 실행 시점에 해당 폴더 안에 있는 `.kit` 파일 탐색을 위해 **apps 폴더 위치**를 정의한다.  
```
# Get path to the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# The apps directory is relative to where the script lives
export EXP_PATH=$SCRIPT_DIR/apps
```
그런 다음에 Isaac Sim의 파이썬 환경 설정 스크립트를 호출한다. 이렇게 해야만 각종 Extension Interface들이 올바르게 로드될 수 있기 때문이다.
```
source ${SCRIPT_DIR}/setup_python_env.sh
```
`setup_python_env.sh`는 다음과 같은 환경 변수들을 설정하거나 갱신한다.
- **ISAAC_PATH** : Isaac의 메인 폴더 경로
- **PYTHONPATH** : 각 Extension의 파이썬 인터페이스를 찾기 위한 경로들
- **LD_LIBRARY_PATH** : 실행할 때 필요한 심볼을 찾기 위해 사용하는 바이너리 라이브러리 경로들
- **CARB_APP_PATH** : 핵심 Omniverse Kit 실행 파일 경로
마지막으로 Omniverse에 함께 포함되어있는 파이썬 인터프리터를 실행한다.
```
python_exe=${PYTHONEXE:-"${SCRIPT_DIR}/kit/python/bin/python3"}
...
$python_exe $@
```

# SimulationApp
[SimulationApp Class](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)는 엔비디아 Isaac Sim application의 생명주기(lifetime)을 관리하기 위한 편의 기능을 제공하는 클래스이다.
## 사용 예제
예제를 통해서 `SimulationApp`을 사용해 어플리케이션을 생성하고, 시간을 한 step 진행시킨 다음, 어플리케이션을 종료해보자.  
> Note!  
> Omniverse 수준의 import는 반드시 SimulationApp 클래스가 인스턴스화가 된 이후에 진행해야 한다.  
> Omniverse API들은 Extension/Runtime 플러그인 시스템을 통해서 제공되기 때문에, 이 시스템들이 먼저 로드되어야 해당 API들을 import 할 수 있다.  
  
> 중요!  
> Headless 모드로 실행하고 싶으면 `"headless": True`를 설정할 것  
```
from isaacsim import SimulationApp

# Simple example showing how to start and stop the helper
simulation_app = SimulationApp({"headless": True})

### Perform any omniverse imports here after the helper loads ###

simulation_app.update()  # Render a single frame
simulation_app.close()  # Cleanup application
```
## SimulationApp은 어떻게 작동하는가?
`SimulationApp`은 어플리케이션을 추가로 설정하고 여러 API를 사용 가능하게 해주지만, 그 이전에 Omniverse-Kit 기반의 implementation이라면 모두 거쳐야 하는 몇단계가 있다. 그 첫번째는 **Carbonite Framework**를 가져오는 것이다. 예를 들어, 여기에서 사용하는 환경변수(`CARB_APP_PATH`, `ISAAC_PATH`, `EXP_PATH` 등) 등은 앞서 `python.sh`를 실행할 때 정의가 된다.
```
import carb
import omni.kit.app

framework = carb.get_framework()
framework.load_plugins(
    loaded_file_wildcards=["omni.kit.app.plugin"],
    search_paths=[os.path.abspath(f'{os.environ["CARB_APP_PATH"]}/kernel/plugins')],
)
```
프레임워크 로딩 이후는, 어플리케이션을 실제 시작하기 전의 **실행인자(start arguments)**를 설정할 수 있다.
```
# Inject a experience config
sys.argv.insert(1, f'{os.environ["EXP_PATH"]}/isaacsim.exp.base.python.kit')

# Add paths to extensions
sys.argv.append(f"--ext-folder")
sys.argv.append(f'{os.path.abspath(os.environ["ISAAC_PATH"])}/exts')

# Run headless
sys.argv.append("--no-window")
```
그리고 나서 어플리케이션을 시작한다.
```
app = omni.kit.app.get_app()
app.startup("Isaac-Sim", os.environ["CARB_APP_PATH"], sys.argv)
```
실행 중인 어플리케이션을 종료하려면 먼저 `shutdown`을 호출한 다음, Framework를 unload하면 된다.
```
app.shutdown()
framework.unload_all_plugins()
```
### 추가 Extension 활성화 하기
방법은 크게 2가지가 있다.
1. Experience File (예를 들어: `apps/isaacsim.exp.base.python.kit`) 에 `[dependencies]` 섹션에 추가
    ```
    # UI에서 Layers와 Stage Window 활성화
    "omni.kit.window.stage" = {}
    "omni.kit.widget.layers" = {}
    ```
2. 파이썬 코드에서 활성화
    ```
    from isaacsim import SimulationApp

    # Start the application
    simulation_app = SimulationApp({"headless": False})

    # Get the utility to enable extensions
    from isaacsim.core.utils.extensions import enable_extension

    # Enable the layers and stage windows in the UI
    enable_extension("omni.kit.widget.stage")
    enable_extension("omni.kit.widget.layers")

    simulation_app.update()
    ```

그 밑의 예제 파일들을 직접 한번 돌려보기를 권장한다.