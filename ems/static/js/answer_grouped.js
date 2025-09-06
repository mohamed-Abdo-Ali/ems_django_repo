document.addEventListener('DOMContentLoaded', () => {
  function setSymbol(btn, expanded) {
    const sym = btn.querySelector('.toggle-symbol');
    if (sym) sym.textContent = expanded ? '−' : '+';
  }

  document.querySelectorAll('.group-toggle').forEach(btn => {
    const targetId = btn.getAttribute('data-target');
    const panel = document.getElementById(targetId);
    if (!panel) return;

    // حالة ابتدائية
    const init = btn.getAttribute('aria-expanded') === 'true';
    setSymbol(btn, init);

    btn.addEventListener('click', () => {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      const next = !expanded;
      btn.setAttribute('aria-expanded', String(next));
      panel.hidden = !next;
      setSymbol(btn, next);
    });
  });
});