# retriever.py
from typing import List, Tuple
from repository import Repository
from domain import Course, Program
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Retriever:
    def __init__(self, repo: Repository):
        self.repo = repo
        self._vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
        self._docs: List[str] = []
        self._meta: List[Tuple[str,str]] = []  # (type, id) -> ("course", name) или ("faq", program_code)

    def build(self):
        docs = []
        meta = []
        # FAQ + about
        for p in self.repo.list_programs():
            blocks = []
            if p.faq_text:
                blocks.append(p.faq_text)
            self._append_doc(docs, meta, "\n\n".join(blocks), ("faq", p.code))
        # Courses
        for c in self.repo.list_courses():
            txt = f"{c.name}\nсеместр: {c.semester or ''}\nтип: {c.type}\nчасы: {c.hours or ''}\nкредиты: {c.credits or ''}\nтеги: {', '.join(c.tags)}\n{c.raw or ''}"
            self._append_doc(docs, meta, txt, ("course", f"{c.program_code}:{c.name}"))
        self._docs = docs
        self._meta = meta
        if self._docs:
            self._X = self._vectorizer.fit_transform(self._docs)
        else:
            from scipy.sparse import csr_matrix
            self._X = csr_matrix((0,0))

    def _append_doc(self, docs, meta, text, idt):
        if text and text.strip():
            docs.append(text)
            meta.append(idt)

    def query(self, q: str, topk: int = 5) -> List[Tuple[float, Tuple[str,str], str]]:
        if not self._docs:
            return []
        qv = self._vectorizer.transform([q])
        sims = cosine_similarity(qv, self._X).ravel()
        idx = sims.argsort()[::-1][:topk]
        return [(float(sims[i]), self._meta[i], self._docs[i]) for i in idx]