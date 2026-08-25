let courseMermaidIndex = 0;

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  htmlLabels: false,
  fontFamily: '"Noto Sans CJK KR", "Noto Sans KR", sans-serif',
  themeVariables: {
    primaryColor: "#dcecff",
    primaryTextColor: "#17324d",
    primaryBorderColor: "#526d82",
    lineColor: "#526d82",
    secondaryColor: "#fff3e0",
    tertiaryColor: "#eef4f8",
  },
});

document$.subscribe(async () => {
  const diagrams = document.querySelectorAll(".course-mermaid:not([data-rendered])");
  for (const diagram of diagrams) {
    const source = diagram.textContent.trim();
    const identifier = `course-mermaid-${courseMermaidIndex}`;
    courseMermaidIndex += 1;
    const { svg } = await mermaid.render(identifier, source);
    diagram.innerHTML = svg;
    diagram.dataset.rendered = "true";
  }
});
