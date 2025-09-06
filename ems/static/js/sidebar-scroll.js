// static/js/sidebar-scroll.js
document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector(".main-sidebar .sidebar");
    if (!sidebar) return;

    // استعادة موضع السكرول السابق
    const savedScroll = localStorage.getItem("jazzmin-sidebar-scroll");
    if (savedScroll) {
        sidebar.scrollTop = parseInt(savedScroll, 10);
    }

    // حفظ الموضع الحالي عند أي تحريك
    sidebar.addEventListener("scroll", function () {
        localStorage.setItem("jazzmin-sidebar-scroll", sidebar.scrollTop);
    });
});









// static/js/reports_center.js
(function(){
  function initSelect2() {
    $('.select2').each(function(){
      const $el = $(this);
      const ddTheme = $el.closest('form').data('dd') || 'sky'; // sky/amber/emerald
      const ddClass = `s2dd-${ddTheme}`;
      $el.select2({
        width: '100%',
        dir: 'rtl',
        language: 'ar',
        placeholder: $el.data('placeholder') || 'اختر...',
        allowClear: true,
        dropdownCssClass: ddClass
      });
    });
  }

  function fillSelect($select, items, textKey='name', valueKey='id') {
    const hadS2 = $select.hasClass('select2-hidden-accessible');
    if (hadS2) $select.select2('destroy');
    $select.empty();
    $select.append(new Option('', '', true, false)).trigger('change'); // placeholder
    items.forEach(it => {
      $select.append(new Option(it[textKey], it[valueKey]));
    });
    initSelect2();
  }

  $(document).ready(function(){
    initSelect2();

    // عناصر تقرير الفصل (داخل نفس النموذج لتجنب تداخل IDs)
    const $fm = $('#form-matrix');
    const $dep = $fm.find('select[name="department"]');
    const $maj = $fm.find('select[name="major"]');
    const $bat = $fm.find('select[name="batch"]');
    const $lvl = $fm.find('select[name="level"]');
    const $sem = $fm.find('select[name="semester"]');
    const $yrM = $fm.find('select[name="year"]');

    $dep.on('change', function(){
      const id = $(this).val();
      if(!id) return;
      $maj.html('<option>جاري التحميل...</option>'); initSelect2();
      $.getJSON('/reports/api/majors/', {department: id}, function(d){
        fillSelect($maj, d.results);
        fillSelect($bat, []); // reset
      });
    });

    $maj.on('change', function(){
      const id = $(this).val();
      if(!id) return;
      $bat.html('<option>جاري التحميل...</option>'); initSelect2();
      $.getJSON('/reports/api/batches/', {major: id}, function(d){
        const items = (d.results || []).map(r => ({id: r.id, name: `${r.order} - ${r.name}`}));
        fillSelect($bat, items);
      });
    });

    $lvl.on('change', function(){
      const id = $(this).val();
      if(!id) return;
      $sem.html('<option>جاري التحميل...</option>'); initSelect2();
      $.getJSON('/reports/api/semesters/', {level: id}, function(d){
        fillSelect($sem, d.results);
      });
    });

    // روابط تصدير تقرير الفصل
    function buildMatrixExport(suffix){
      const base = $fm.data('export-base'); // /reports/matrix/
      const major = $maj.val(), semester = $sem.val(), batch = $bat.val(), year = $yrM.val();
      if(!(major && semester && batch && year)) return '#';
      return `${base}major/${major}/semester/${semester}/batch/${batch}/year/${year}/${suffix}`;
    }
    $('#mx-pdf').on('click', function(){ $(this).attr('href', buildMatrixExport('pdf/')); });
    $('#mx-excel').on('click', function(){ $(this).attr('href', buildMatrixExport('excel/')); });
    $('#mx-csv').on('click', function(){ $(this).attr('href', buildMatrixExport('csv/')); });

    // عناصر سجل المقرر
    const $fc = $('#form-course');
    const $course = $fc.find('select[name="course"]');
    const $yrC = $fc.find('select[name="year"]');

    function buildCourseExport(suffix){
      const base = $fc.data('export-base'); // /reports/course/
      const c = $course.val(), y = $yrC.val();
      if(!(c && y)) return '#';
      return `${base}${c}/year/${y}/${suffix}`;
    }
    $('#cr-pdf').on('click', function(){ $(this).attr('href', buildCourseExport('pdf/')); });
    $('#cr-excel').on('click', function(){ $(this).attr('href', buildCourseExport('excel/')); });
    $('#cr-csv').on('click', function(){ $(this).attr('href', buildCourseExport('csv/')); });
  });
})();