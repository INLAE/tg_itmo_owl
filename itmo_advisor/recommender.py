# recommender.py
from typing import List
from domain import Course
from collections import defaultdict

class ElectiveRecommender:
    """
    Простая объяснимая эвристика:
    - маппим бэкграунд и цели в набор приоритетных тегов
    - фильтруем элективы по тегам
    - ранжируем: совпадения тегов, затем упоминание 'проект/практикум', затем кредиты/часы
    """
    def __init__(self):
        self.background_map = {
            "junior_ml": {"mlops","cv","nlp","genai","bigdata"},
            "data_engineer": {"bigdata","cloud","mlops"},
            "product_manager": {"product","pm","genai","data"},
            "backend": {"cloud","mlops","arch","bigdata"},
            "research": {"genai","nlp","cv","data"},
        }

    def recommend(self, courses: List[Course], background_key: str, limit: int = 8) -> List[Course]:
        pri = self.background_map.get(background_key, set())
        elect = [c for c in courses if c.type == "elective" or "по выбору" in (c.raw or "").lower()]
        def score(c: Course):
            tags = set(c.tags or [])
            match = len(tags & pri)
            project_bonus = 1 if ("проект" in (c.name.lower()) or "практикум" in (c.name.lower())) else 0
            credits = c.credits or 0.0
            hours = c.hours or 0
            return (match, project_bonus, credits, hours)
        elect.sort(key=score, reverse=True)
        return elect[:limit]