# qa.py
from typing import Tuple, List
from repository import Repository
from retriever import Retriever
from guard import is_in_domain

class QAService:
    def __init__(self, repo: Repository, retriever: Retriever):
        self.repo = repo
        self.ret = retriever

    def answer(self, program_code: str, question: str) -> str:
        if not is_in_domain(question):
            return "Хэй! Я отвечаю только на вопросы по обучению на магистерских программах «Искусственный интеллект» и «AI Product» ИТМО. Переформулируйте, пожалуйста, в рамках темы."
        # уточнение: если программа не выбрана — отвечаем по обеим
        hits = self.ret.query(question, topk=5)
        # если пусто — честный ответ
        if not hits:
            return "Не нашёл ответа в учебных планах и описании программ. Попробуйте перефразировать или спросить о других деталях обучения."
        parts: List[str] = []
        for score, (typ, mid), doc in hits:
            if typ == "faq":
                parts.append(f"• Из FAQ программы: {doc.splitlines()[0]}")
            elif typ == "course":
                pg, name = mid.split(":",1)
                if program_code and pg != program_code:
                    continue
                parts.append(f"• Курс «{name}» — возможно релевантно вашему вопросу")
        if not parts:
            return "Не нашёл точного ответа, но могу помочь с навигацией по курсам и FAQ."
        return "\n".join(parts[:5])