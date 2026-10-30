"""
وحدة القواعد الدينية الثابتة.
توفر دوال للتحقق من النصوص بناءً على قواعد قطعية.
"""
from .fixed_rules import check_fixed_rules, get_rule_explanation

__all__ = ['check_fixed_rules', 'get_rule_explanation']
