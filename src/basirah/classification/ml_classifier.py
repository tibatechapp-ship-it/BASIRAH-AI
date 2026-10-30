"""مصنف النصوص باستخدام التعلم الآلي (Naive Bayes) مع القواعد الثابتة."""

import logging
from typing import Dict, Tuple, List, Optional
import pickle
from pathlib import Path

from basirah.models.categories import CATEGORIES
from basirah.utils.helpers import normalize_arabic_text
from basirah.rules.fixed_rules import check_fixed_rules

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import LabelEncoder
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("مكتبة scikit-learn غير متوفرة. سيتم استخدام طريقة الكلمات المفتاحية فقط.")


class MLTextClassifier:
    """مصنف النصوص الهجين (قواعد ثابتة + كلمات مفتاحية + تعلم آلي)."""
    
    def __init__(self, use_fixed_rules: bool = True, use_ml: bool = True):
        """تهيئة المصنف.
        
        Args:
            use_fixed_rules: استخدام القواعد الثابتة للتحقق الأولي (افتراضي: True).
            use_ml: استخدام نموذج ML إذا كان متاحاً (افتراضي: True).
        """
        self.categories = CATEGORIES
        self.use_fixed_rules = use_fixed_rules
        self.use_ml = use_ml and ML_AVAILABLE
        self.model: Optional[Pipeline] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.is_trained = False
        
        if self.use_ml:
            logger.info("تم تهيئة مصنف النصوص مع دعم التعلم الآلي")
        else:
            logger.info("تم تهيئة مصنف النصوص (بدون تعلم آلي)")
    
    def train(self, texts: List[str], labels: List[str]) -> bool:
        """تدريب نموذج التعلم الآلي.
        
        Args:
            texts: قائمة النصوص للتدريب.
            labels: قائمة التصنيفات المقابلة.
            
        Returns:
            bool: True إذا نجح التدريب، False otherwise.
        """
        if not ML_AVAILABLE or not self.use_ml:
            logger.warning("التعلم الآلي غير متاح. لا يمكن تدريب النموذج.")
            return False
        
        if not texts or not labels:
            logger.error("قائمة النصوص أو التصنيفات فارغة")
            return False
        
        if len(texts) != len(labels):
            logger.error("عدد النصوص لا يطابق عدد التصنيفات")
            return False
        
        try:
            # ترميز التصنيفات
            self.label_encoder = LabelEncoder()
            encoded_labels = self.label_encoder.fit_transform(labels)
            
            # إنشاء خط أنابيب TF-IDF + Naive Bayes
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95
                )),
                ('clf', MultinomialNB())
            ])
            
            # تدريب النموذج
            self.model.fit(texts, encoded_labels)
            self.is_trained = True
            
            logger.info(f"تم تدريب نموذج ML بنجاح على {len(texts)} عينة")
            return True
            
        except Exception as e:
            logger.error(f"حدث خطأ أثناء تدريب النموذج: {e}", exc_info=True)
            return False
    
    def save_model(self, model_path: str) -> bool:
        """حفظ النموذج المدرب إلى ملف.
        
        Args:
            model_path: مسار حفظ النموذج.
            
        Returns:
            bool: True إذا نجح الحفظ، False otherwise.
        """
        if not self.is_trained:
            logger.error("النموذج لم يتم تدريبه بعد")
            return False
        
        try:
            model_data = {
                'model': self.model,
                'label_encoder': self.label_encoder,
                'categories': list(self.label_encoder.classes_)
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"تم حفظ النموذج إلى: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"حدث خطأ أثناء حفظ النموذج: {e}", exc_info=True)
            return False
    
    def load_model(self, model_path: str) -> bool:
        """تحميل نموذج مدرب من ملف.
        
        Args:
            model_path: مسار ملف النموذج.
            
        Returns:
            bool: True إذا نجح التحميل، False otherwise.
        """
        if not Path(model_path).exists():
            logger.error(f"ملف النموذج غير موجود: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.is_trained = True
            
            logger.info(f"تم تحميل النموذج من: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"حدث خطأ أثناء تحميل النموذج: {e}", exc_info=True)
            return False
    
    def classify(self, text: str, normalized: bool = True) -> Tuple[str, float]:
        """تصنيف النص إلى فئة معروفة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            tuple: (اسم الفئة، درجة التطابق).
        """
        return classify_hybrid(
            text, 
            normalized, 
            self.use_fixed_rules,
            self.model if self.is_trained else None,
            self.label_encoder
        )
    
    def classify_with_details(self, text: str, normalized: bool = True) -> Dict:
        """تصنيف النص مع إرجاع تفاصيل كاملة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية.
        """
        return classify_hybrid_with_details(
            text, 
            normalized, 
            self.use_fixed_rules,
            self.model if self.is_trained else None,
            self.label_encoder
        )


def _normalize_keywords(keywords: List[str]) -> List[str]:
    """تطبيع قائمة الكلمات المفتاحية."""
    return [normalize_arabic_text(kw) for kw in keywords]


def classify_hybrid(
    text: str, 
    normalized: bool = True, 
    use_fixed_rules: bool = True,
    ml_model: Optional[Pipeline] = None,
    label_encoder: Optional[LabelEncoder] = None
) -> Tuple[str, float]:
    """تصنيف النص باستخدام هجين من القواعد الثابتة والكلمات المفتاحية وML.
    
    الاستراتيجية:
    1. التحقق من القواعد الثابتة القطعية (دقة 100%).
    2. إذا كان نموذج ML مدرباً، استخدامه للحصول على تصنيف.
    3. إذا لم يكن ML متاحاً، استخدام طريقة الكلمات المفتاحية.
    
    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
        use_fixed_rules: استخدام القواعد الثابتة أولاً.
        ml_model: نموذج ML المدرب (اختياري).
        label_encoder: مُرمِّز التصنيفات (اختياري).
    
    Returns:
        tuple: (اسم الفئة أو 'غير_مصنف', درجة التطابق).
    """
    if not text or not isinstance(text, str):
        logger.warning("تم استلام نص فارغ أو غير صالح للتصنيف")
        return ("غير_مصنف", 0.0)
    
    try:
        # الخطوة 1: التحقق من القواعد الثابتة القطعية
        if use_fixed_rules:
            fixed_result = check_fixed_rules(text)
            if fixed_result:
                category, confidence = fixed_result
                logger.info(f"تم التصنيف بواسطة القواعد الثابتة: {category} (دقة: {confidence*100}%)")
                return (category, confidence)
            logger.debug("لم تطبق أي قاعدة ثابتة، جاري استخدام ML أو الكلمات المفتاحية")
        
        # الخطوة 2: استخدام ML إذا كان متاحاً ومدرّباً
        if ml_model is not None and label_encoder is not None:
            try:
                pred = ml_model.predict([text])[0]
                proba = ml_model.predict_proba([text])[0]
                confidence = float(max(proba))
                category = label_encoder.inverse_transform([pred])[0]
                
                logger.info(f"تم التصنيف بواسطة ML: {category} (دقة: {confidence*100}%)")
                return (category, confidence)
            except Exception as e:
                logger.warning(f"فشل تصنيف ML، العودة للكلمات المفتاحية: {e}")
        
        # الخطوة 3: استخدام طريقة الكلمات المفتاحية
        if normalized:
            text = normalize_arabic_text(text)
            logger.debug("تم تطبيع النص قبل التصنيف")
        
        scores: Dict[str, int] = {}
        for category, keywords in CATEGORIES.items():
            normalized_keywords = _normalize_keywords(keywords) if normalized else keywords
            score = sum(text.count(keyword) for keyword in normalized_keywords)
            scores[category] = score
        
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        logger.info(f"نتائج التصنيف بالكلمات المفتاحية: {best_category} بدرجة {best_score}")
        
        if best_score == 0:
            logger.info("لم يتم العثور على أي تطابق للكلمات المفتاحية")
            return ("غير_مصنف", 0.0)
        
        confidence_score = min(best_score / 10.0, 1.0)
        return (best_category, confidence_score)
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تصنيف النص: {e}", exc_info=True)
        return ("غير_مصنف", 0.0)


def classify_hybrid_with_details(
    text: str, 
    normalized: bool = True,
    use_fixed_rules: bool = True,
    ml_model: Optional[Pipeline] = None,
    label_encoder: Optional[LabelEncoder] = None
) -> Dict:
    """تصنيف النص مع إرجاع تفاصيل كاملة عن النتائج.
    
    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
        use_fixed_rules: استخدام القواعد الثابتة أولاً.
        ml_model: نموذج ML المدرب.
        label_encoder: مُرمِّز التصنيفات.
    
    Returns:
        dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية، ومنهجية التصنيف.
    """
    fixed_result = None
    if use_fixed_rules:
        fixed_result = check_fixed_rules(text)
    
    if fixed_result:
        category, confidence = fixed_result
        explanations = []
        if use_fixed_rules:
            from basirah.rules.fixed_rules import get_rule_explanation
            explanations = get_rule_explanation(text)
        
        result = {
            "category": category,
            "score": confidence,
            "all_scores": {cat: 0 for cat in CATEGORIES.keys()},
            "is_classified": True,
            "method": "fixed_rules",
            "explanations": explanations
        }
        logger.debug(f"تفاصيل التصنيف (قواعد ثابتة): {result}")
        return result
    
    # محاولة استخدام ML
    if ml_model is not None and label_encoder is not None:
        try:
            pred = ml_model.predict([text])[0]
            proba = ml_model.predict_proba([text])[0]
            category = label_encoder.inverse_transform([pred])[0]
            confidence = float(max(proba))
            
            result = {
                "category": category,
                "score": confidence,
                "all_scores": {cat: float(p) for cat, p in zip(label_encoder.classes_, proba)},
                "is_classified": True,
                "method": "ml",
                "explanations": []
            }
            logger.debug(f"تفاصيل التصنيف (ML): {result}")
            return result
        except Exception as e:
            logger.warning(f"فشل ML، العودة للكلمات المفتاحية: {e}")
    
    # استخدام الكلمات المفتاحية
    from basirah.classification.classifier import classify_with_details as keyword_classify
    result = keyword_classify(text, normalized, use_fixed_rules=False)
    result["method"] = "keywords_fallback"
    return result


# دوال مساعدة للتدريب السريع
def create_training_sample(text: str, category: str) -> Dict:
    """إنشاء عينة تدريب.
    
    Args:
        text: النص.
        category: التصنيف.
    
    Returns:
        dict: عينة التدريب.
    """
    return {"text": text, "label": category}


def train_from_samples(samples: List[Dict]) -> MLTextClassifier:
    """تدريب مصنف من عينات جاهزة.
    
    Args:
        samples: قائمة العينات [{'text': ..., 'label': ...}, ...].
    
    Returns:
        MLTextClassifier: المصنف المدرب.
    """
    classifier = MLTextClassifier(use_fixed_rules=True, use_ml=True)
    
    texts = [s["text"] for s in samples]
    labels = [s["label"] for s in samples]
    
    classifier.train(texts, labels)
    return classifier
