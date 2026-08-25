window.MathJax = {
  loader: { load: ["[tex]/ams"] },
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    packages: { "[+]": ["ams"] },
    processEscapes: true,
    processEnvironments: true,
  },
  svg: { fontCache: "global" },
  options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" },
};

document$.subscribe(() => {
  MathJax.typesetPromise();
});
