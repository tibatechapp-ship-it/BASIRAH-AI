<p align="center">
  <img src="https://img.shields.io/badge/BASIRAH--AI-%D8%A8%D8%B5%D9%8A%D8%B1%D8%A9-2EA043?style=for-the-badge" alt="بصيرة">
</p>

# بصيرة — BASIRAH-AI

> **منصة ذكاء الوثائق العربية** — من أرشيف مبعثر وممسوح ضوئياً إلى قاعدة معرفية مصنفة وقابلة للبحث الدلالي. OCR عربي حقيقي + embeddings على pgvector — كله مفتوح المصدر ويعمل على جهازك.

[![ci](https://github.com/tibatechapp-ship-it/BASIRAH-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/tibatechapp-ship-it/BASIRAH-AI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 ما هي بصيرة؟ ولمن؟ (من خط معالجة إلى منصة)

- **المشكلة**: المكتبات الرقمية والأبحاث العربية تصل كملفات مبعثرة (PDF/EPUB/HTML/ممسوحات) بلا فهرسة معرفية — قيمتها المحتملة مهدورة.
- **ما هو الآن**: خط معالجة ذكي كامل — استخراج OCR → تصنيف هجين (قواعد + كلمات مفتاحية + ML) → تخزين معرفي على **pgvector** ببحث دلالي عربي — بواجهات ثلاث (CLI/سطح مكتب/ويب RTL) وحزمة Docker Compose.
- **المنتج المستهدف**: **منصة معرفية** فوق هذا الخط — مقياس جودة استرجاع معلن، لوحة بيانات وصفية، إزالة تكرار دلالية أذكى — معلن في [خارطة المنتَجة](https://github.com/tibatechapp-ship-it/vixona-github-profile/blob/main/docs/productization-plan.md)، والخط الحالي أساسه الصلب.
- **لمن**: المكتبات والجامعات ومراكز البحث والناشرين العرب الذين يملكون أرشيفاً ورقياً/رقمياً ويريدون تحويله إلى أصل معرفي قابل للبحث — **بأدوات مفتوحة تحفظ خصوصية بياناتهم**، لا سحابة تقرأ وثائقهم.
- **وعدٌ مميز**: معظم أدوات البحث الدلالي لا تفهم العربية بجدية (تطبيع الهمزات والتشكيل، OCR عربي جاد). بصيرة وُلدت لهذه الفجوة — عربية أولاً بلا ترجمة لاحقة.

## ✅ يعمل اليوم — بالدليل (2026-10-31)

| القدرة | الدليل القابل للتحقق |
|---|---|
| CI أخضر يشمل طبقة pgvector | [ci.yml](.github/workflows/ci.yml) يثبّت المتطلبات الكاملة ويجري الاختبارات فوق مكدس PostgreSQL/embeddings |
| بحث دلالي عربي حقيقي | `GET /documents/search?q=...` عبر pgvector — موثق أدناه بأوامر التشغيل |
| لوحة بيانات وصفية | `/dashboard` عربية RTL بلا JS + `/api/dashboard/stats` (العدد، توزيع المواضيع، التغطية الدلالية) + بحث تفاعلي يعلن نوعه (دلالي/نصي) — **10 اختبارات (52/52)** مع Escape كامل |
| تصنيف هجين | قواعد قطعية + كلمات مفتاحية بتطبيع عربي + Naive Bayes/TF-IDF قابل للتدريب والحفظ |
| OCR للصور | PNG/JPG/JPEG/TIFF/BMP/GIF بالعربية والإنجليزية (Tesseract) |
| Docker stack كامل | `docker compose up --build` يرفع PostgreSQL+pgvector وFastAPI معاً |
| واجهات ثلاث | CLI + Tkinter سطح مكتب + Streamlit ويب RTL |
| 6 صيغ قراءة | PDF, TXT, DOCX, EPUB, HTML + الصور (OCR) |

## 🗺️ البنية

```
src/
└── basirah/
    ├── cli.py               واجهة سطر الأوامر
    ├── organizer.py         المنظم الرئيسي
    ├── classification/
    │   ├── classifier.py    مصنف النصوص (قواعد + كلمات مفتاحية)
    │   └── ml_classifier.py مصنف التعلم الآلي (Naive Bayes + TF-IDF)
    ├── gui/app.py           تطبيق Tkinter
    ├── io/
    │   ├── file_handler.py  قراءة PDF/TXT/DOCX/EPUB/HTML والصور (OCR)
    │   └── mover.py         نقل الملفات
    ├── models/categories.py فئات التصنيف وصيغ الملفات (Enum)
    ├── reports/generator.py مولد تقارير المكتبة
    ├── rules/fixed_rules.py محرك القواعد القطعية
    └── utils/helpers.py     تطبيع النص العربي
src/api/                    خادم FastAPI + pgvector (الرفع والفهرسة والبحث الدلالي)
src/gui.py                  واجهة Streamlit ويب (RTL)
tests/                      جناح الاختبارات (خلايا التصنيف، IO، API)
```

## 🚀 البدء في 60 ثانية

```bash
pip install -r requirements.txt
# لدعم OCR: ثبّت Tesseract + حزمة اللغة العربية على نظامك

# نظّم مكتبة كاملة من سطر الأوامر
PYTHONPATH=src python -m basirah.cli

# أو عبر Docker — خادم + قاعدة متجهات جاهزان
docker compose up --build
# ثم: http://localhost:8000/docs
```

### كوحدة برمجية

```python
from basirah import organize_library
from basirah.classification import classify, MLTextClassifier, train_from_samples

total, classified = organize_library("/path/to/library")

category, score = classify("الصلاة والزكاة")   # → الفقه

samples = [
    {"text": "كتاب عن الفقه الإسلامي", "label": "فقه"},
    {"text": "حديث شريف عن النبي", "label": "حديث"},
]
ml = train_from_samples(samples)
ml.save_model("model.pkl")                     # تدريب وحفظ وتحميل النموذج
```

### خادم API الدلالي

```bash
docker compose up --build
# PostgreSQL+pgvector على 5432 — FastAPI على 8000
```

| نقطة النهاية | الوظيفة |
|---|---|
| `GET /health` | التحقق من حالة النظام |
| `POST /documents/upload` | رفع مستند وفهرسته دلالياً |
| `GET /documents/` | قائمة المستندات المفهرسة |
| `GET /documents/search?q=...` | **البحث الدلالي بالعربية** |
| `POST /library/organize` | رفع أرشيف ZIP وتنظيمه تلقائياً |

### واجهة الويب (Streamlit)

```bash
streamlit run src/gui.py
```

واجهة عربية RTL: رفع مكتبة مضغوطة (ZIP) وتنظيم تلقائي، اكتشاف المكررات، وعرض هيكل المكتبة المصنفة.

## 🧪 الاختبارات

```bash
PYTHONPATH=src pytest tests/ -v
```

> الحالة بصدق: كتلة الاختبارات أصغر مما تستحقه المنصة (خلايا التصنيف والإدخال/الإخراج مغطاة؛ طبقة API تُختبر في CI بكامل متطلباتها). أول معلم في [خارطة المنتَجة](https://github.com/tibatechapp-ship-it/vixona-github-profile/blob/main/docs/productization-plan.md) هو **مقياس جودة استرجاع معلن** (Recall@5 على مجموعة استعلامات ذهبية) — فجعل الجودة قابلة للقياس لا للادعاء.

## 🗺️ خارطة الطريق

### المنجز ✓
- [x] قراءة 6 صيغ + OCR عربي/إنجليزي
- [x] تصنيف هجين (قواعد + كلمات + ML قابل للتدريب)
- [x] إزالة المكرر + معالجة تصادم الأسماء
- [x] واجهات: CLI + Tkinter + Streamlit RTL
- [x] خادم FastAPI + pgvector: رفع وفهرسة و**بحث دلالي عربي**
- [x] Docker stack كامل + CI أخضر

### التالي — بالشراكة مع خارطة المحفظة
- [ ] **مقياس جودة استرجاع** في CI (Recall@5 / MRR — 20 استعلاماً ذهبياً)
- [ ] **لوحة بيانات وصفية**: توزيع المواضيع، الكيانات، بحث تفاعلي
- [ ] تطبيع التشكيل/الهمزات قبل الفهرسة + دمج أذكى للمكررات الدلالية
- [ ] ضبط chunking للعربية (حدود الجمل والعناوين)
- [ ] رسم علاقات بين المستندات
- [ ] OCR كامل للكتب متعددة الصفحات

## 📄 الترخيص

MIT — انظر [LICENSE](LICENSE). © 2026 Vixona Technologies (tibatechapp-ship-it)

## 🧭 المكان في المحفظة

بصيرة درجة خامسة في [محفظة TibaTech](https://github.com/tibatechapp-ship-it/vixona-github-profile) — [بطاقة الأداء](https://github.com/tibatechapp-ship-it/vixona-github-profile/blob/main/docs/scorecard.md) · [خارطة المنتَجة](https://github.com/tibatechapp-ship-it/vixona-github-profile/blob/main/docs/productization-plan.md). التوثيق التفصيلي: [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md).
