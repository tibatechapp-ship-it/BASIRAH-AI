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
    │   └── classifier.py    # مصنف النصوص
    ├── io/                  # وحدة الإدخال والإخراج
    │   ├── __init__.py
    │   ├── file_handler.py  # قراءة PDF و TXT و DOCX
    │   └── mover.py         # نقل الملفات
    ├── models/              # نماذج البيانات
    │   ├── __init__.py
    │   └── categories.py    # فئات التصنيف (Enum)
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
- **دعم صيغ متعددة**: PDF, TXT, DOCX
- **محرك قواعد ثابتة** للتعرف القطعي على النصوص الدينية
- **تصنيف بالكلمات المفتاحية** مع تطبيع النص العربي
- **إنشاء المجلدات تلقائياً**
- **معالجة التصادم في أسماء الملفات**
- **نظام تقارير وتحسينات** في جودة الكود

### تحسينات Quality of Life

- استخدام `Enum` للفئات لصيانة أفضل
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

## الاستخدام

### من سطر الأوامر:

```bash
PYTHONPATH=src python -m basirah.cli
```

### كوحدة برمجية:

```python
from basirah import organize_library
from basirah.classification import classify, classify_with_details

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
from basirah.classification import TextClassifier
classifier = TextClassifier(use_fixed_rules=True, min_confidence=0.1)
result = classifier.classify("حديث رسول الله صلى الله عليه وسلم")
```

### دعم صيغ الملفات:

```python
from basirah.io import extract_text, read_docx

# استخراج نص من أي ملف مدعوم
text = extract_text("book.pdf")
text = extract_text("notes.txt")
text = extract_text("document.docx")  # جديد!

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

- [x] دعم DOCX
- [x] تحسين جودة الكود (Type Hints, TypedDict)
- [x] استخدام Enum للفئات
- [x] إضافة فئة "الحديث" للتصنيف
- [x] توسيع الكلمات المفتاحية

### الإصدار 0.3

- [ ] إزالة المكرر
- [ ] تقارير وإحصائيات متقدمة
- [ ] واجهة رسومية (GUI)

### الإصدار 1.0

- [ ] اكتشاف العلاقات بين الملفات
- [ ] البحث الدلالي
- [ ] OCR للكتب المصورة
- [ ] تطبيق سطح مكتب
- [ ] تطبيق أندرويد

## المساهمة

نرحب بالمساهمات في المشروع! يرجى فتح Issue أو Pull Request.

## الترخيص

[أضف معلومات الترخيص هنا]
