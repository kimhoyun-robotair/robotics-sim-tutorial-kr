# 수학·도식·이미지 렌더링 Fixture

이 페이지는 문서 렌더링 파이프라인을 반복해서 검사하기 위한 저장소 소유 fixture이다. 튜토리얼 본문이 아니라 수식, Mermaid, 반응형 이미지가 strict MkDocs와 실제 브라우저에서 계속 렌더링되는지 확인하는 회귀 검사 페이지이다.

## 번호가 있는 수식

운동 에너지는 다음처럼 표시된다.

\[
E_k = \frac{1}{2}mv^2 \tag{1}
\]

## Mermaid 도식

<pre class="course-mermaid">
flowchart LR
    A[명령 입력] --> B[Gazebo 시뮬레이션]
    B --> C[관측 결과]
</pre>

## 반응형 이미지와 한국어 설명

<figure class="course-figure">
  <img src="../../assets/diagrams/rendering-fixture.svg" alt="좌표계에서 로봇의 이동 방향을 보여 주는 재현 가능한 도식" loading="lazy">
  <figcaption>그림 1. 로봇, x축, 진행 방향을 구분해 확인하는 재현 가능한 시각 자료이다.</figcaption>
</figure>

검증기는 수식의 MathJax glyph, Mermaid 안의 세 label, 이미지 대체 텍스트, caption, 화면 너비 초과 여부를 확인한다. 이 요소를 바꿀 때에는 `docs/assets/manifest.yaml`의 fixture metadata와 browser route 검증도 함께 갱신해야 한다.
