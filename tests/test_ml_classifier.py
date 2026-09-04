"""اختبارات مصنف التعلم الآلي."""

import pytest
import tempfile
from pathlib import Path

from basirah.classification.ml_classifier import (
    MLTextClassifier,
    classify_hybrid,
    create_training_sample,
    train_from_samples
)


@pytest.fixture
def sample_training_data():
    """بيانات تدريب بسيطة للاختبار."""
    samples = [
        {"text": "هذا كتاب عن الفقه الإسلامي وأحكام الصلاة والزكاة", "label": "فقه"},
        {"text": "حديث شريف عن رسول الله صلى الله عليه وسلم", "label": "حديث"},
        {"text": "تفسير القرآن الكريم وسورة البقرة", "label": "تفسير"},
        {"text": "سيرة النبي محمد صلى الله عليه وسلم", "label": "سيرة"},
        {"text": "كتاب الفقه الحنفي والمالكي", "label": "فقه"},
        {"text": "صحيح البخاري ومسلم من كتب الحديث", "label": "حديث"},
        {"text": "تفسير ابن كثير للقرآن", "label": "تفسير"},
        {"text": "سيرة الصحابة والتابعين", "label": "سيرة"},
    ]
    return samples


def test_ml_classifier_init():
    """اختبار تهيئة المصنف."""
    classifier = MLTextClassifier(use_fixed_rules=True, use_ml=True)
    assert classifier.use_fixed_rules is True
    assert classifier.is_trained is False


def test_ml_classifier_train(sample_training_data):
    """اختبار تدريب المصنف."""
    texts = [s["text"] for s in sample_training_data]
    labels = [s["label"] for s in sample_training_data]
    
    classifier = MLTextClassifier(use_ml=True)
    result = classifier.train(texts, labels)
    
    # قد يفشل إذا لم تكن sklearn متوفرة
    if result:
        assert classifier.is_trained is True
        assert classifier.model is not None


def test_ml_classifier_classify_without_training():
    """اختبار التصنيف بدون تدريب (يجب استخدام الكلمات المفتاحية)."""
    classifier = MLTextClassifier(use_ml=True)
    category, score = classifier.classify("هذا كتاب فقه إسلامي")
    
    assert isinstance(category, str)
    assert isinstance(score, float)


def test_ml_classifier_save_load_model(sample_training_data):
    """اختبار حفظ وتحميل النموذج."""
    texts = [s["text"] for s in sample_training_data]
    labels = [s["label"] for s in sample_training_data]
    
    classifier = MLTextClassifier(use_ml=True)
    trained = classifier.train(texts, labels)
    
    if trained:
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
            model_path = tmp.name
        
        # حفظ النموذج
        save_result = classifier.save_model(model_path)
        assert save_result is True
        assert Path(model_path).exists()
        
        # تحميل النموذج في مصنف جديد
        new_classifier = MLTextClassifier(use_ml=True)
        load_result = new_classifier.load_model(model_path)
        assert load_result is True
        assert new_classifier.is_trained is True
        
        # تنظيف
        Path(model_path).unlink()


def test_create_training_sample():
    """اختبار إنشاء عينة تدريب."""
    sample = create_training_sample("نص اختبار", "تفسير")
    assert sample == {"text": "نص اختبار", "label": "تفسير"}


def test_train_from_samples(sample_training_data):
    """اختبار التدريب من عينات جاهزة."""
    classifier = train_from_samples(sample_training_data)
    # قد لا يكون مدرباً إذا لم تكن sklearn متوفرة
    assert isinstance(classifier, MLTextClassifier)


def test_classify_hybrid_with_fixed_rules():
    """اختبار التصنيف الهجين مع القواعد الثابتة."""
    # نص ينطبق عليه قاعدة ثابتة
    text = "البخاري صحيح"
    category, score = classify_hybrid(text, normalized=True, use_fixed_rules=True)
    
    assert isinstance(category, str)
    assert isinstance(score, float)


def test_classify_hybrid_without_ml():
    """اختبار التصنيف الهجين بدون ML."""
    text = "هذا كتاب عن الفقه الإسلامي"
    category, score = classify_hybrid(
        text, 
        normalized=True, 
        use_fixed_rules=True,
        ml_model=None,
        label_encoder=None
    )
    
    assert isinstance(category, str)
    assert isinstance(score, float)


def test_classify_hybrid_empty_text():
    """اختبار التصنيف مع نص فارغ."""
    category, score = classify_hybrid("", use_fixed_rules=True)
    assert category == "غير_مصنف"
    assert score == 0.0


def test_classify_hybrid_none_text():
    """اختبار التصنيف مع None."""
    category, score = classify_hybrid(None, use_fixed_rules=True)
    assert category == "غير_مصنف"
    assert score == 0.0
