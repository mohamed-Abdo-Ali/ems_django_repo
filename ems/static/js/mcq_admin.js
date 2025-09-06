document.addEventListener('DOMContentLoaded', function () {
  const max = 6;
  const minVisible = 3;

  // أيقونات Heroicons (Tailwind Icons) كـ SVG
  function heroXIcon(size = 16) {
    return `
      <svg xmlns="http://www.w3.org/2000/svg" class="mcq-icon" viewBox="0 0 24 24" fill="none" width="${size}" height="${size}">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M6 18L18 6M6 6l12 12"/>
      </svg>
    `;
  }

  function heroTrashIcon(size = 16) {
    // سلة مهملات (Outline). إن حبيت هذه بدلاً من X، غيّر btn.innerHTML أدناه.
    return `
      <svg xmlns="http://www.w3.org/2000/svg" class="mcq-icon" viewBox="0 0 24 24" fill="none" width="${size}" height="${size}">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8"
              d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m1 0l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0h8m-5 4v6m4-6v6"/>
      </svg>
    `;
  }

  const name = i => `choice_${i}`;
  const inputOf = i => document.getElementById(`id_${name(i)}`);
  const correctSelect = document.getElementById('id_correct_choice');

  // العثور على صف الحقل (يدعم Django Admin + Jazzmin)
  function rowOf(i) {
    const inp = inputOf(i);
    if (!inp) return null;
    return inp.closest('.form-row') || inp.closest('.form-group') || inp.parentElement;
  }

  function isHidden(row) {
    return row?.classList.contains('mcq-hidden');
  }

  function showField(i) {
    const r = rowOf(i);
    if (r) r.classList.remove('mcq-hidden');
  }

  function hideField(i) {
    const r = rowOf(i);
    if (r) r.classList.add('mcq-hidden');
  }

  // لفّ الحقل داخل حاوية مرنة لتكون الأيقونة بجانبه
  function ensureInlineWrapper(i) {
    const inp = inputOf(i);
    if (!inp) return null;
    let wrapper = inp.closest('.mcq-inline');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.className = 'mcq-inline';
      inp.parentNode.insertBefore(wrapper, inp);
      wrapper.appendChild(inp);
    }
    return wrapper;
  }

  // إنشاء زر حذف كأيقونة صغيرة بجانب الحقل (للخيارات > 3 فقط)
  function ensureDeleteButton(i) {
    const row = rowOf(i);
    const inp = inputOf(i);
    if (!row || !inp) return null;

    const wrapper = ensureInlineWrapper(i);
    if (!wrapper) return null;

    let btn = wrapper.querySelector(`.mcq-del-btn[data-index="${i}"]`);
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'button btn btn-outline-danger btn-sm mcq-del-btn';
      btn.setAttribute('data-index', String(i));
      btn.setAttribute('title', 'حذف هذا الخيار');

      // اختر الأيقونة التي تفضّلها:
      btn.innerHTML = heroXIcon(16);         // افتراضي: X
      // أو بدّل للسلة:
      // btn.innerHTML = heroTrashIcon(16);

      // ضع الزر داخل الحاوية بجانب الحقل
      wrapper.appendChild(btn);

      btn.addEventListener('click', function () {
        const idx = parseInt(btn.getAttribute('data-index') || '0', 10);
        if (!idx || idx <= minVisible) return; // لا تحذف 1..3

        hideField(idx);
        const input = inputOf(idx);
        if (input) input.value = '';

        placeButton();
        updateDeleteButtons();
        rebuildCorrectOptions();
      });
    }
    return btn;
  }

  function updateDeleteButtons() {
    for (let i = 1; i <= max; i++) {
      const row = rowOf(i);
      const btn = ensureDeleteButton(i);
      if (!row || !btn) continue;

      // عرض زر الحذف فقط للخيارات المرئية (>3)
      if (i <= minVisible || isHidden(row)) {
        btn.style.display = 'none';
      } else {
        btn.style.display = 'inline-flex';
      }
    }
  }

  // إخفِ 4..6 إذا كانت فارغة، وأظهر 1..3 دائماً
  for (let i = 4; i <= max; i++) {
    const v = (inputOf(i)?.value || '').trim();
    if (v) showField(i); else hideField(i);
  }
  for (let i = 1; i <= minVisible; i++) showField(i);

  // أنشئ أزرار الحذف مبدئيًا ولفّ الحقول
  for (let i = 1; i <= max; i++) {
    ensureInlineWrapper(i);
    ensureDeleteButton(i);
  }

  function visibleCount() {
    let c = 0;
    for (let i = 1; i <= max; i++) {
      const r = rowOf(i);
      if (r && !isHidden(r)) c++;
    }
    return c;
  }

  // بناء قائمة "الإجابة الصحيحة" من نصوص الخيارات الفعلية الظاهرة
  function rebuildCorrectOptions() {
    if (!correctSelect) return;

    const prev = correctSelect.value;
    correctSelect.innerHTML = '';

    for (let i = 1; i <= max; i++) {
      const r = rowOf(i);
      if (!r || isHidden(r)) continue;

      const txt = (inputOf(i)?.value || '').trim();
      const opt = document.createElement('option');
      opt.value = String(i);                  // نحافظ على مؤشر الحقل الحقيقي
      let label = txt || `الاختيار ${i}`;    // احتياطي لو فاضي
      if (label.length > 60) label = label.slice(0, 60) + '…';
      opt.textContent = label;
      correctSelect.appendChild(opt);
    }

    const values = Array.from(correctSelect.options).map(o => o.value);
    correctSelect.value = values.includes(prev) ? prev : (values[0] || '');
  }

  // زر "إضافة خيار +" + ملاحظة الحد الأقصى
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.className = 'button btn btn-outline-primary mcq-add-btn';
  addBtn.textContent = 'إضافة خيار +';

  const note = document.createElement('div');
  note.className = 'mcq-note';
  note.textContent = 'لقد وصلت إلى الحد الأقصى لعدد الإجابات الممكنة للسؤال';

  function placeButton() {
    let last = 1;
    for (let i = 1; i <= max; i++) {
      const r = rowOf(i);
      if (r && !isHidden(r)) last = i;
    }
    const lastRow = rowOf(last);
    if (lastRow && lastRow.parentNode) {
      // انقل الزر والملاحظة ليكونا بعد آخر صف ظاهر
      lastRow.parentNode.insertBefore(addBtn, lastRow.nextSibling);
      addBtn.parentNode.insertBefore(note, addBtn.nextSibling);
    }

    const atMax = visibleCount() >= max;
    addBtn.disabled = atMax;
    note.style.display = atMax ? 'block' : 'none'; // إظهار الملاحظة عند الحد الأقصى
  }

  addBtn.addEventListener('click', function () {
    const vis = visibleCount();
    if (vis >= max) return;
    showField(vis + 1);
    placeButton();
    updateDeleteButtons();
    rebuildCorrectOptions();
  });

  // أول تشغيل
  updateDeleteButtons();
  rebuildCorrectOptions();
  placeButton();

  // تحديث العناوين عند الكتابة/التغيير
  for (let i = 1; i <= max; i++) {
    const inp = inputOf(i);
    if (inp) {
      inp.addEventListener('input', rebuildCorrectOptions);
      inp.addEventListener('change', rebuildCorrectOptions);
    }
  }
});