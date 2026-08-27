# 수학·도식·이미지 렌더링 Fixture

이 페이지는 문서 렌더링 파이프라인을 반복해서 검사하기 위한 저장소 소유 fixture입니다.

## 번호가 있는 수식

운동 에너지는 다음처럼 표시됩니다.

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
  <figcaption>그림 1. 로봇, x축, 진행 방향을 구분해 확인하는 재현 가능한 시각 자료입니다.</figcaption>
</figure>
