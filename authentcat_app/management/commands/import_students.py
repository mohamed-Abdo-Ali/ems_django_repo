from django.core.management.base import BaseCommand
import pandas as pd
from conttroll_app.models import student_report_from_uivercity, Acdimaic_and_term_from_uivercity


class Command(BaseCommand):
    help = "استيراد بيانات الطلاب + السنة والترم من ملف إكسل"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="مسار ملف الإكسل")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]

        # قراءة الشيت (ورقة1) واستخدام أول صف كأعمدة
        df = pd.read_excel(file_path, sheet_name="ورقة1", header=1)

        # تنظيف أسماء الأعمدة (إزالة المسافات أول وآخر النص)
        df.columns = df.columns.str.strip()

        # إعادة ترقيم الصفوف ليبدأ من 1 بدلاً من رقم الصف الفعلي في الإكسل
        df.reset_index(drop=True, inplace=True)

        # --------------------------
        # 1) إدخال بيانات السنة والترم
        # --------------------------
        unique_academic_terms = df[["السنة الدراسية", "الترم"]].dropna().drop_duplicates()

        for _, row in unique_academic_terms.iterrows():
            Acdimaic_and_term_from_uivercity.objects.get_or_create(
                Acdimaic_year=row["السنة الدراسية"],
                Acdimaic_year_semester=row["الترم"]
            )

        # --------------------------
        # 2) إدخال بيانات الطلاب
        # --------------------------
        count = 0
        for _, row in df.iterrows():
            if pd.isna(row["اسم الطالب"]):  # نتجاهل الصفوف الفارغة
                continue

            student_report_from_uivercity.objects.create(
                name=row["اسم الطالب"],
                gender=row["النوع"],
                univercity_number=int(row["الرقم الجامعي"]),
                major=row["التخصص"],
                semester_id=int(row["الفصل الدراسي"])
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ تم إدخال {count} طالب + الفصول الدراسية بنجاح"))
