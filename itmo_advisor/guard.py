# guard.py
from typing import Optional

ALLOWED_THEMES = [
    "итмо", "магистратур", "мастер", "ai", "искусствен", "продукт", "поступлен", "экзамен",
    "учебн", "план", "курс", "семестр", "зачет", "з.е", "ects", "расписан", "стипенд", "стажиров",
    "электив", "по выбору", "портфолио", "вкрд", "вкрд", "вкрд".replace("вкрд","вкр") # ВКР
]
def is_in_domain(question: str) -> bool:
    ql = question.lower()
    return any(k in ql for k in ALLOWED_THEMES)