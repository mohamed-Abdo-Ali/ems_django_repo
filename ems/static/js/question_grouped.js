document.addEventListener('DOMContentLoaded', () => {
  const toggles = document.querySelectorAll('.exam-toggle');

  function setSymbol(btn, expanded) {
    const sym = btn.querySelector('.toggle-symbol');
    if (!sym) return;
    // استخدم الرمز المناسب: + عند الإغلاق، − عند الفتح
    sym.textContent = expanded ? '−' : '+';
  }

  // اربط لكل زر
  toggles.forEach(btn => {
    const targetId = btn.getAttribute('data-target');
    const panel = document.getElementById(targetId);
    if (!panel) return;

    // ضبط الرمز الابتدائي (aria-expanded="false" => +)
    const expandedInit = btn.getAttribute('aria-expanded') === 'true';
    setSymbol(btn, expandedInit);

    btn.addEventListener('click', () => {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      const next = !expanded;
      btn.setAttribute('aria-expanded', String(next));
      panel.hidden = !next ? true : false; // إذا فتحنا => hidden=false
      setSymbol(btn, next);
    });
  });
});