# bot_telegram.py
import os
from typing import Dict
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from repository import Repository
from retriever import Retriever
from qa import QAService
from dialog import UserState, WELCOME, BACKGROUND_HELP, map_background
from recommender import ElectiveRecommender

class TelegramBot:
    def __init__(self, token: str, repo: Repository, retriever: Retriever):
        self.repo = repo
        self.ret = retriever
        self.qa = QAService(repo, retriever)
        self.reco = ElectiveRecommender()
        self.app = Application.builder().token(token).build()
        self.state: Dict[int, UserState] = {}
        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.on_start))
        self.app.add_handler(CommandHandler("sync", self.on_sync))
        self.app.add_handler(CommandHandler("switch", self.on_switch))
        self.app.add_handler(CommandHandler("recommend", self.on_recommend))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))

    async def on_start(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = upd.effective_user.id
        self.state[uid] = UserState()
        await upd.message.reply_text(WELCOME)

    async def on_switch(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = upd.effective_user.id
        st = self.state.setdefault(uid, UserState())
        st.program_code = None
        await upd.message.reply_text("Ок, выберем программу заново. Напишите ai или ai_product.")

    async def on_sync(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        from scraper import ItmoProgramScraper
        from curriculum_parser import CurriculumParser
        s = ItmoProgramScraper(self.repo)
        s.full_sync()
        parser = CurriculumParser(self.repo)
        for p in self.repo.list_programs():
            courses = parser.parse_for_program(p.code)
            self.repo.replace_courses(p.code, courses)
        self.ret.build()
        await upd.message.reply_text("Данные обновлены. Задавайте вопросы!")

    async def on_recommend(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = upd.effective_user.id
        st = self.state.setdefault(uid, UserState())
        if not st.program_code:
            await upd.message.reply_text("Сначала выберите программу: ai или ai_product")
            return
        if not st.background_key:
            await upd.message.reply_text(BACKGROUND_HELP)
            return
        courses = self.repo.list_courses(st.program_code)
        recs = self.reco.recommend(courses, st.background_key, limit=6)
        if not recs:
            await upd.message.reply_text("Пока не нашёл подходящих элективов в плане. Попробуйте другой бэкграунд.")
            return
        msg = "Рекомендованные элективы под ваш профиль:\n" + "\n".join(
            [f"• {c.name} (семестр {c.semester or '—'}, теги: {', '.join(c.tags) or '—'})" for c in recs]
        )
        await upd.message.reply_text(msg)

    async def on_text(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = upd.effective_user.id
        st = self.state.setdefault(uid, UserState())
        text = upd.message.text.strip()

        if st.program_code is None:
            if text.lower() in ("ai", "ai_product"):
                st.program_code = text.lower()
                await upd.message.reply_text(
                    f"Вы выбрали программу: {st.program_code}. Теперь расскажите про ваш бэкграунд.\n{BACKGROUND_HELP}"
                )
            else:
                await upd.message.reply_text("Напишите: ai или ai_product.")
            return

        if st.background_key is None:
            bg = map_background(text)
            if bg:
                st.background_key = bg
                await upd.message.reply_text(f"Отлично, учту ваш профиль: {bg}. Задавайте вопросы по обучению или вызовите /recommend.")
            else:
                await upd.message.reply_text(BACKGROUND_HELP)
            return

        # Вопросы по программе
        ans = self.qa.answer(st.program_code, text)
        await upd.message.reply_text(ans)

    def run(self):
        self.app.run_polling()