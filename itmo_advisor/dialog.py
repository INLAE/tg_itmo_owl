# dialog.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserState:
    program_code: Optional[str] = None     # "ai" | "ai_product"
    background_key: Optional[str] = None   # см. recommender.py
    stage: str = "welcome"

WELCOME = ("Привет! Я помогу выбрать между программами ИТМО «Искусственный интеллект» и «AI Product», "
           "объясню различия, подскажу по учебным планам и порекомендую элективы под ваш бэкграунд.\n\n"
           "Напишите: ai — если интересует «Искусственный интеллект»,\n"
           "или ai_product — «Управление ИИ-продуктами». "
           "Позже можно поменять выбор командой /switch.")

BACKGROUND_HELP = ("Расскажите кратко про ваш бэкграунд. Варианты: "
                   "junior_ml, data_engineer, product_manager, backend, research. "
                   "Можно одной фразой: «я джун ML, хочу в прод» — я распознаю.")

def map_background(text: str) -> Optional[str]:
    t = text.lower()
    if "product" in t or "продукт" in t or "pm" in t:
        return "product_manager"
    if "ml" in t or "data scientist" in t or "джун" in t:
        return "junior_ml"
    if "data eng" in t or "инженер данных" in t:
        return "data_engineer"
    if "backend" in t or "бэкенд" in t:
        return "backend"
    if "research" in t or "ресерч" in t or "наука" in t:
        return "research"
    return None