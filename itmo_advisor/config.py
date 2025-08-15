# config.py
from dataclasses import dataclass
import os

AI_URL = "https://abit.itmo.ru/program/master/ai"
AI_PRODUCT_URL = "https://abit.itmo.ru/program/master/ai_product"

DATA_DIR = os.environ.get("DATA_DIR", "data")
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "itmo_advisor.db"))
USER_AGENT = "Mozilla/5.0 (itmo-advisor-bot)"
REQUEST_TIMEOUT = 25

@dataclass(frozen=True)
class ProgramConfig:
    code: str
    name: str
    url: str

PROGRAMS = [
    ProgramConfig(code="ai", name="Искусственный интеллект", url=AI_URL),
    ProgramConfig(code="ai_product", name="Управление ИИ-продуктами (AI Product)", url=AI_PRODUCT_URL),
]