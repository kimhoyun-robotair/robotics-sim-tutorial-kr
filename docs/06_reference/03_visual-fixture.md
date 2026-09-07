# 수학·도식·이미지 표시 확인용 페이지

이 페이지는 문서 표시 기능을 검사하는 고정 예제(fixture)다. 문서를 수정한 뒤에도 수식·Mermaid 도식·이미지가 제대로 보이는지 확인한다. `mkdocs build --strict`로 빌드 오류를 검사하고, 실제 브라우저에서 화면 크기를 바꿔 표시 결과를 확인한다.

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

자동 검사는 MathJax가 그린 수식, 도식 안의 세 문구, 이미지 대체 텍스트와 설명, 화면 너비를 넘는 요소가 있는지 확인한다. 이 예제를 바꿀 때에는 `docs/assets/manifest.yaml`의 관련 항목과 브라우저 검사 조건도 함께 갱신한다.
