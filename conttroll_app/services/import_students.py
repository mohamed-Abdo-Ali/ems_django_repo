# # conttroll_app/services/import_students.py
# import pandas as pd
# from conttroll_app.models import student_report_from_uivercity, Acdimaic_and_term_from_uivercity

# REQUIRED_COLUMNS = {"اسم الطالب", "النوع", "الرقم الجامعي", "التخصص", "الفصل الدراسي", "السنة الدراسية", "الترم"}

# def _to_int(value, field_name):
#     try:
#         # يدعم قيم مثل "500", "500.0", 500, 500.0
#         return int(float(str(value).strip()))
#     except Exception:
#         raise ValueError(f"القيمة في العمود '{field_name}' غير صالحة: {value}")

# def import_students_from_excel(file_obj, sheet_name="ورقة1", header_row=1):
#     # قراءة الإكسل
#     df = pd.read_excel(file_obj, sheet_name=sheet_name, header=header_row)
#     df.columns = df.columns.astype(str).str.strip()
#     df.reset_index(drop=True, inplace=True)

#     # التحقق من الأعمدة المطلوبة
#     missing = REQUIRED_COLUMNS - set(df.columns)
#     if missing:
#         raise ValueError(f"الأعمدة التالية مفقودة في الملف: {', '.join(missing)}")

#     # 1) إدخال السنة والترم
#     unique_academic_terms = df[["السنة الدراسية", "الترم"]].dropna(how="any").drop_duplicates()
#     terms_created = 0
#     for _, row in unique_academic_terms.iterrows():
#         _, created = Acdimaic_and_term_from_uivercity.objects.get_or_create(
#             Acdimaic_year=row["السنة الدراسية"],
#             Acdimaic_year_semester=row["الترم"],
#         )
#         if created:
#             terms_created += 1

#     # 2) إدخال الطلاب
#     students_created = 0
#     for _, row in df.iterrows():
#         if pd.isna(row["اسم الطالب"]) or str(row["اسم الطالب"]).strip() == "":
#             continue

#         univercity_number = _to_int(row["الرقم الجامعي"], "الرقم الجامعي")
#         semester_id = _to_int(row["الفصل الدراسي"], "الفصل الدراسي")

#         student_report_from_uivercity.objects.create(
#             name=str(row["اسم الطالب"]).strip(),
#             gender=str(row["النوع"]).strip(),
#             univercity_number=univercity_number,
#             major=str(row["التخصص"]).strip(),
#             semester_id=semester_id,
#         )
#         students_created += 1

#     return {
#         "rows": len(df),
#         "terms_created": terms_created,
#         "students_created": students_created,
#     }



# conttroll_app/services/import_students.py
import pandas as pd
from conttroll_app.models import student_report_from_uivercity, Acdimaic_and_term_from_uivercity

REQUIRED_COLUMNS = {"اسم الطالب", "النوع", "الرقم الجامعي", "التخصص", "الفصل الدراسي", "السنة الدراسية", "الترم"}

def _to_int(value, field_name):
    try:
        return int(float(str(value).strip()))
    except Exception:
        raise ValueError(f"القيمة في العمود '{field_name}' غير صالحة: {value}")

def import_students_from_excel(file_obj, sheet_name="ورقة1", header_row=1):
    df = pd.read_excel(file_obj, sheet_name=sheet_name, header=header_row)
    df.columns = df.columns.astype(str).str.strip()
    df.reset_index(drop=True, inplace=True)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"الأعمدة التالية مفقودة في الملف: {', '.join(missing)}")

    # 1) السنة والترم
    unique_academic_terms = df[["السنة الدراسية", "الترم"]].dropna(how="any").drop_duplicates()
    terms_created = 0
    for _, row in unique_academic_terms.iterrows():
        _, created = Acdimaic_and_term_from_uivercity.objects.get_or_create(
            Acdimaic_year=row["السنة الدراسية"],
            Acdimaic_year_semester=row["الترم"],
        )
        if created:
            terms_created += 1

    # 2) الطلاب
    students_created = 0
    created_ids = []
    for _, row in df.iterrows():
        if pd.isna(row["اسم الطالب"]) or str(row["اسم الطالب"]).strip() == "":
            continue

        univercity_number = _to_int(row["الرقم الجامعي"], "الرقم الجامعي")
        semester_id = _to_int(row["الفصل الدراسي"], "الفصل الدراسي")

        obj = student_report_from_uivercity.objects.create(
            name=str(row["اسم الطالب"]).strip(),
            gender=str(row["النوع"]).strip(),
            univercity_number=univercity_number,
            major=str(row["التخصص"]).strip(),
            semester_id=semester_id,
        )
        students_created += 1
        created_ids.append(obj.pk)

    return {
        "rows": len(df),
        "terms_created": terms_created,
        "students_created": students_created,
        "created_ids": created_ids,  # مهم
    }