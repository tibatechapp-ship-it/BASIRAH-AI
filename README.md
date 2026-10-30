# BASIRAH-AI

بصيرة منصة معرفية ذكية تهدف إلى تحويل المكتبات الرقمية والبحوث العلمية من ملفات مبعثرة إلى قاعدة معرفية منظمة وقابلة للبحث والتحليل.

## الرؤية

الانتقال من إدارة الملفات إلى إدارة المعرفة.

## البنية الجديدة

تمت إعادة هيكلة الكود باستخدام بنية معيارية:

```
src/
└── basirah/
    ├── __init__.py          # نقطة الدخول الرئيسية
    ├── cli.py               # واجهة سطر الأوامر
    ├── organizer.py         # المنظم الرئيسي
    ├── classification/      # وحدة التصنيف
    │   ├── __init__.py
    │   ├── classifier.py    # مصنف النصوص (قواعد + كلمات مفتاحية)
    │   └── ml_classifier.py # مصنف التعلم الآلي (Naive Bayes + TF-IDF)
    ├── gui/                 # الواجهة الرسومية
    │   ├── __init__.py
    │   └── app.py           # تطبيق Tkinter
    ├── io/                  # وحدة الإدخال والإخراج
    │   ├── __init__.py
    │   ├── file_handler.py  # قراءة PDF و TXT و DOCX و EPUB و HTML والصور (OCR)
    │   └── mover.py         # نقل الملفات
    ├── models/              # نماذج البيانات
    │   ├── __init__.py
    │   └── categories.py    # فئات التصنيف وصيغ الملفات (Enum)
    ├── reports/             # التقارير والإحصاءات
    │   ├── __init__.py
    │   └── generator.py     # مولد تقارير المكتبة
    ├── rules/               # القواعد الثابتة
    │   ├── __init__.py
    │   └── fixed_rules.py   # محرك القواعد الدينية
    └── utils/               # دوال مساعدة
        ├── __init__.py
        └── helpers.py       # تطبيع النص العربي
```

## المميزات

### الإصدار الحالي (0.2)

- **تصنيف المحتوى** حسب الموضوع (القرآن، العقيدة، الفقه، السيرة، الحديث)
- **دعم صيغ متعددة**: PDF, TXT, DOCX, EPUB, HTML
- **دعم OCR للصور** والملفات الممسوحة ضوئياً (PNG, JPG, JPEG, TIFF, BMP, GIF) بالعربية والإنجليزية
- **محرك قواعد ثابتة** للتعرف القطعي على النصوص الدينية
- **تصنيف بالكلمات المفتاحية** مع تطبيع النص العربي
- **تحسين دقة التصنيف باستخدام التعلم الآلي** (Naive Bayes + TF-IDF) مع تصنيف هجين
- **حفظ وتحميل نماذج ML المدربة**
- **تقارير وإحصائيات** عن حالة المكتبة
- **واجهة رسومية** (Tkinter)
- **إنشاء المجلدات تلقائياً**
- **معالجة التصادم في أسماء الملفات**

### تحسينات Quality of Life

- استخدام `Enum` للفئات وصيغ الملفات لصيانة أفضل
- `TypedDict` لنتائج التصنيف
- دعم كامل لـ Type Hints
- معالجة أخطاء محسنة
- سجلات تفصيلية (Logging)

## التثبيت

```bash
pip install -r requirements.txt
```

أو باستخدام Conda:

```bash
conda env create -f environment.yml
conda activate basirah-ai
```

ملاحظة: لدعم OCR تحتاج إلى تثبيت محرك Tesseract على النظام مع حزمة اللغة العربية.

## الاستخدام

### من سطر الأوامر:

```bash
PYTHONPATH=src python -m basirah.cli
```

### الواجهة الرسومية:

```bash
PYTHONPATH=src python -c "from basirah.gui.app import run_gui; run_gui()"
```

### كوحدة برمجية:

```python
from basirah import organize_library
from basirah.classification import classify, classify_with_details, TextClassifier
from basirah.classification import MLTextClassifier, train_from_samples

# تنظيم مكتبة
total, classified = organize_library("/path/to/library")

# تصنيف نص
category, score = classify("الصلاة والزكاة")
print(category)  # الفقه

# تصنيف مع التفاصيل
details = classify_with_details("العقيدة والتوحيد")
print(details)
# {
#     "category": "العقيدة",
#     "score": 0.2,
#     "all_scores": {...},
#     "is_classified": True,
#     "method": "keywords",
#     "explanations": []
# }

# استخدام المصنف ككائن
classifier = TextClassifier(use_fixed_rules=True, min_confidence=0.1)
result = classifier.classify("حديث رسول الله صلى الله عليه وسلم")

# استخدام التعلم الآلي للتصنيف
samples = [
    {"text": "كتاب عن الفقه الإسلامي", "label": "فقه"},
    {"text": "حديث شريف عن النبي", "label": "حديث"},
]
ml_classifier = train_from_samples(samples)
category_ml, confidence = ml_classifier.classify("هذا كتاب فقهي")
print(f"التصنيف: {category_ml}, الدقة: {confidence}")

# حفظ وتحميل النموذج
ml_classifier.save_model("model.pkl")
new_classifier = MLTextClassifier()
new_classifier.load_model("model.pkl")
```

### دعم صيغ الملفات:

```python
from basirah.io import extract_text, read_docx

# استخراج نص من أي ملف مدعوم
text = extract_text("book.pdf")
text = extract_text("notes.txt")
text = extract_text("document.docx")
text = extract_text("ebook.epub")
text = extract_text("page.html")
text = extract_text("scanned_page.png")  # OCR

# قراءة مباشرة
text = read_docx("document.docx")
```

## الاختبارات

```bash
PYTHONPATH=src pytest tests/ -v
```

## خارطة الطريق

### الإصدار 0.1 ✓

- [x] قراءة PDF و TXT
- [x] تصنيف أولي للكتب
- [x] إنشاء المجلدات تلقائياً
- [x] إعادة هيكلة الكود

### الإصدار 0.2 ✓

- [x] إزالة المكرر
- [x] دعم DOCX
- [x] دعم EPUB و HTML
- [x] دعم OCR للصور (PNG, JPG, JPEG, TIFF, BMP, GIF)
- [x] تحسين دقة التصنيف بالتعلم الآلي
- [x] تحسين جودة الكود (Type Hints, TypedDict)
- [x] استخدام Enum للفئات
- [x] إضافة فئة "الحديث" للتصنيف
- [x] توسيع الكلمات المفتاحية
- [x] تقارير وإحصائيات
- [x] واجهة رسومية (GUI)

### الإصدار 0.3

- [ ] تدريب نماذج ML على بيانات إسلامية موسعة
- [ ] تقارير إحصائية متقدمة (رسوم بيانية)

### الإصدار 1.0

- [ ] اكتشاف العلاقات بين الملفات
- [ ] البحث الدلالي
- [ ] OCR كامل للكتب المصورة متعددة الصفحات
- [ ] تطبيق سطح مكتب
- [ ] تطبيق أندرويد

## المساهمة

نرحب بالمساهمات في المشروع! يرجى فتح Issue أو Pull Request.

## الترخيص

[أضف معلومات الترخيص هنا]
