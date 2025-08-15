# curriculum_parser.py
import os, re
from typing import List
from domain import Course
from repository import Repository
from config import DATA_DIR

# Мы не знаем точный формат планов, поэтому делаем устойчивый к PDF/DOCX парсер.
# Поддержка PDF: pdfminer.six; DOCX: python-docx. Если план не скачался, парсим текст страницы.

class CurriculumParser:
    def __init__(self, repo: Repository):
        self.repo = repo

    def _parse_text_lines(self, text: str) -> List[Course]:
        # эвристики: строки со схемой "семестр X", тип курса в скобках, часы/зачёты числами
        courses: List[Course] = []
        current_sem = None
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            m_sem = re.search(r"семестр[:\s]*(\d+)", s, flags=re.I)
            if m_sem:
                current_sem = int(m_sem.group(1))
                continue
            # Матчим "Название курса (электив)" или "Название курса — 3 з.е."
            name = re.sub(r"\s{2,}", " ", re.sub(r"[\u00A0]", " ", s))
            if len(name) < 4:
                continue
            m_cred = re.search(r"(\d+[.,]?\d*)\s*(з\.?е\.?|ECTS|кред)", s, flags=re.I)
            m_hours = re.search(r"(\d+)\s*(час(ов|а)?|ч\.)", s, flags=re.I)
            ctype = "elective" if re.search(r"(электив|по выбору)", s, flags=re.I) else "core"
            credits = float(m_cred.group(1).replace(",", ".")) if m_cred else None
            hours = int(m_hours.group(1)) if m_hours else None
            # Фильтр вероятных заголовков
            if any(k in s.lower() for k in ["партнеры программы", "карьера", "вопросы", "как поступить"]):
                continue
            # грубая эвристика — пропустим строки слишком общие
            if len(s.split()) <= 2 and credits is None and hours is None:
                continue
            courses.append(Course(program_code="", name=name, semester=current_sem, type=ctype, hours=hours, credits=credits, raw=s))
        return courses

    def _extract_text_from_pdf(self, path: str) -> str:
        from pdfminer.high_level import extract_text
        return extract_text(path)

    def _extract_text_from_docx(self, path: str) -> str:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    def parse_for_program(self, program_code: str) -> List[Course]:
        # 1) пробуем файл плана, если есть
        plan_dir = os.path.join(DATA_DIR, "plans")
        text = ""
        if os.path.isdir(plan_dir):
            for name in os.listdir(plan_dir):
                if name.startswith(program_code):
                    p = os.path.join(plan_dir, name)
                    try:
                        if name.lower().endswith(".pdf"):
                            text = self._extract_text_from_pdf(p)
                        elif name.lower().endswith(".docx"):
                            text = self._extract_text_from_docx(p)
                    except Exception:
                        text = ""
                    break
        if not text:
            # 2) fallback: берём HTML страницы и чистим от тегов
            prog = self.repo.get_program(program_code)
            if prog and prog.about_html:
                import bs4
                soup = bs4.BeautifulSoup(prog.about_html, "html.parser")
                text = soup.get_text(separator="\n")
        courses = self._parse_text_lines(text)
        # проставим program_code и простые теги
        enriched: List[Course] = []
        for c in courses:
            c.program_code = program_code
            low = c.name.lower()
            tags = []
            for kw, tag in [
                ("mlops", "mlops"),
                ("production", "production"),
                ("data", "data"),
                ("vision", "cv"),
                ("computer vision", "cv"),
                ("nlp", "nlp"),
                ("генератив", "genai"),
                ("продукт", "product"),
                ("менедж", "pm"),
                ("архитектур", "arch"),
                ("big data", "bigdata"),
                ("облач", "cloud"),
            ]:
                if kw in low:
                    tags.append(tag)
            c.tags = tags
            enriched.append(c)
        return enriched