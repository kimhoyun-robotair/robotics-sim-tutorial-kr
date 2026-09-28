# OpenUSD란 뭘까?
OpenUSD (Universal Scene Description)은 픽사에서 개발되었으며, USD를 다루기 위한 오픈소스 프레임워크이다. USD는 [이 파일](00_USD가_뭐지_간단한_소개.md)에서 공부를 했듯이, 3D scene에 대해서 Describing / Composing / Simulating / Collaborating 을 하기 위해서 개발된 포맷/시스템이다.  
  
OpenUSD가 가지고 있는 고유한 특성, 그리고 이점은 다음과 같다.
- **Non-Destructive Collaboration**
  - 기본적으로 3D scene에 대해서 단일 파일로 뭉개서 합쳐버리는 것이 아니라, 다수의 레이어를 compose 하는 방식으로 작동하기 때문에 각 작업자는 자신의 작업 범위에 해당하는 레이어만 골라서 수정하면 된다. 따라서 원본 파일을 파괴하지 않고도 작동한다.
- **Modularity and Scalability**
  - USD는 3D scene에 대해서 module 단위로 쪼개서, Reference / Instance / Share 하기 때문에 modularity 그리고 scalability가 장점이다.
- **Cross-Application Interoperability**
  - 다양한 3D 제작 프로그램(예: 블렌더)에서 모두 호환 가능한 포맷이고, 프레임워크이다.