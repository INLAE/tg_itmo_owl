# scraper.py
import re, time, os
from typing import Tuple, Optional
import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT, DATA_DIR, PROGRAMS
from domain import Program
from repository import Repository

HEADERS = {"User-Agent": USER_AGENT}

class ItmoProgramScraper:
    def __init__(self, repo: Repository):
        self.repo = repo

    def _get(self, url: str) -> str:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text

    def _find_plan_link(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        # Ищем ссылку по тексту или по расширению
        for a in soup.find_all("a"):
            text = (a.get_text() or "").strip().lower()
            href = a.get("href") or ""
            if "учебный план" in text or "план обучения" in text or re.search(r"\.(pdf|docx?)$", href):
                if href.startswith("/"):
                    return f"https://abit.itmo.ru{href}"
                if href.startswith("http"):
                    return href
        return None

    def _extract_faq_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        # Собираем вопросы/ответы FAQ с заголовками уровня h5/h6 и следующими блоками
        faq_chunks = []
        for h in soup.find_all(["h5", "h6"]):
            txt = (h.get_text() or "").strip()
            if not txt:
                continue
            if any(k in txt.lower() for k in ["вопрос", "экзамен", "как", "можно ли", "чем", "будет ли", "уровень", "сможу ли"]):
                # захват следующего абзаца
                nxt = h.find_next_sibling()
                body = (nxt.get_text() if nxt else "") if hasattr(nxt, "get_text") else ""
                faq_chunks.append(f"{txt}\n{body}")
        return "\n\n".join(faq_chunks)

    def sync_program(self, code: str, name: str, url: str) -> Program:
        html = self._get(url)
        plan_url = self._find_plan_link(html)
        faq_text = self._extract_faq_text(html)
        p = Program(code=code, name=name, url=url, plan_url=plan_url, about_html=html, faq_text=faq_text)
        self.repo.upsert_program(p)
        return p

    def download_plan(self, program: Program) -> Optional[str]:
        if not program.plan_url:
            return None
        os.makedirs(os.path.join(DATA_DIR, "plans"), exist_ok=True)
        ext = os.path.splitext(program.plan_url.split("?")[0])[-1] or ".pdf"
        path = os.path.join(DATA_DIR, "plans", f"{program.code}{ext}")
        try:
            r = requests.get(program.plan_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            return path
        except Exception:
            return None

    def full_sync(self) -> None:
        for cfg in PROGRAMS:
            p = self.sync_program(cfg.code, cfg.name, cfg.url)
            time.sleep(0.5)
            self.download_plan(p)