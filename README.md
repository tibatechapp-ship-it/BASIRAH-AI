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
    │   └── categories.py    # فئات التصنيف
    └── utils/               # دوال مساعدة
        ├── __init__.py
        └── helpers.py       # دوال مساعدة عامة
```

## المميزات

- تصنيف المحتوى حسب الموضوع (القرآن، العقيدة، الفقه، السيرة)
- دعم ملفات PDF و TXT و DOCX والصور (OCR)
- دعم OCR للصور والملفات الممسوحة ضوئياً (العربية والإنجليزية)
- تحسين دقة التصنيف باستخدام التعلم الآلي (Naive Bayes + TF-IDF)
- إنشاء المجلدات تلقائياً
- معالجة التصادم في أسماء الملفات
- حفظ وتحميل نماذج ML المدربة

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
from basirah import organize_library, classify
from basirah.classification import MLTextClassifier, train_from_samples

# تنظيم مكتبة
total, classified = organize_library("/path/to/library")

# تصنيف نص
category = classify("الصلاة والزكاة")
print(category)  # الفقه

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
- [x] دعم OCR للصور (PNG, JPG, TIFF, BMP, GIF)
- [x] تحسين دقة التصنيف بالتعلم الآلي
- [ ] تقارير وإحصائيات

### الإصدار 0.3

- [ ] واجهة رسومية
- [ ] تدريب نماذج ML على بيانات إسلامية موسعة

### الإصدار 1.0

- [ ] اكتشاف العلاقات بين الملفات
- [ ] البحث الدلالي
- [ ] تطبيق سطح مكتب
- [ ] تطبيق أندرويد

## الترخيص

[أضف معلومات الترخيص هنا]
