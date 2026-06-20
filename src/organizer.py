import os
import shutil
import fitz

# --------------------------
# التصنيفات الأولية
# --------------------------

CATEGORIES = {
    "الحديث": [
        "حدثنا",
        "أخبرنا",
        "رواه",
        "صحيح البخاري",
        "صحيح مسلم",
        "السنن"
    ],

    "التفسير": [
        "تفسير",
        "أسباب النزول",
        "الآية",
        "السورة",
        "القراءات"
    ],

    "العقيدة": [
        "العقيدة",
        "التوحيد",
        "الإيمان",
        "الأسماء والصفات"
    ],

    "الفقه": [
        "الطهارة",
        "الصلاة",
        "الزكاة",
        "الصيام",
        "الحج",
        "البيع"
    ],

    "السيرة": [
        "السيرة",
        "الغزوات",
        "الهجرة",
        "رسول الله"
    ]
}


# --------------------------
# قراءة PDF
# --------------------------

def read_pdf(pdf_path):

    try:

        document = fitz.open(pdf_path)

        text = ""

        for page in document:

            text += page.get_text()

            if len(text) > 50000:
                break

        document.close()

        return text

    except Exception:

        return ""


# --------------------------
# قراءة TXT
# --------------------------

def read_txt(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return f.read()

    except Exception:

        return ""


# --------------------------
# استخراج النص
# --------------------------

def extract_text(file_path):

    ext = os.path.splitext(
        file_path
    )[1].lower()

    if ext == ".pdf":
        return read_pdf(file_path)

    if ext == ".txt":
        return read_txt(file_path)

    return ""


# --------------------------
# التصنيف
# --------------------------

def classify(text):

    scores = {}

    for category, keywords in CATEGORIES.items():

        score = 0

        for keyword in keywords:

            score += text.count(keyword)

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:

        return "غير_مصنف"

    return best_category


# --------------------------
# إنشاء مجلد
# --------------------------

def ensure_folder(path):

    os.makedirs(
        path,
        exist_ok=True
    )


# --------------------------
# نقل الملف
# --------------------------

def move_file(
    source,
    target_folder
):

    ensure_folder(
        target_folder
    )

    filename = os.path.basename(
        source
    )

    destination = os.path.join(
        target_folder,
        filename
    )

    counter = 1

    while os.path.exists(
        destination
    ):

        name, ext = os.path.splitext(
            filename
        )

        destination = os.path.join(
            target_folder,
            f"{name}_{counter}{ext}"
        )

        counter += 1

    shutil.move(
        source,
        destination
    )


# --------------------------
# التنظيم
# --------------------------

def organize_library(
    library_path
):

    total_files = 0

    classified_files = 0

    for filename in os.listdir(
        library_path
    ):

        file_path = os.path.join(
            library_path,
            filename
        )

        if not os.path.isfile(
            file_path
        ):
            continue

        ext = os.path.splitext(
            filename
        )[1].lower()

        if ext not in [
            ".pdf",
            ".txt"
        ]:
            continue

        total_files += 1

        print(
            f"فحص الملف: {filename}"
        )

        text = extract_text(
            file_path
        )

        category = classify(
            text
        )

        target_folder = os.path.join(
            library_path,
            category
        )

        move_file(
            file_path,
            target_folder
        )

        classified_files += 1

        print(
            f"تم التصنيف -> {category}"
        )

    print("\n")
    print("=" * 40)
    print("انتهى التصنيف")
    print("=" * 40)
    print(
        f"عدد الملفات: {total_files}"
    )
    print(
        f"عدد الملفات المصنفة: {classified_files}"
    )


# --------------------------
# التشغيل
# --------------------------

if __name__ == "__main__":

    print(
        "\nBASIRAH AI v0.1\n"
    )

    library = input(
        "أدخل مسار المكتبة: "
    )

    organize_library(
        library
    )