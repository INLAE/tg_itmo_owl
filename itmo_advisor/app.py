import argparse, os, sys
from utils import load_env, build_repo
from scraper import ItmoProgramScraper
from curriculum_parser import CurriculumParser
from retriever import Retriever
from bot_telegram import TelegramBot

def main():
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="Скачать страницы/планы и распарсить")
    parser.add_argument("--bot", action="store_true", help="Запуск Telegram бота")
    parser.add_argument("--cli", action="store_true", help="Консольный режим (без Telegram)")
    args = parser.parse_args()

    repo = build_repo()

    if args.sync:
        scraper = ItmoProgramScraper(repo)
        scraper.full_sync()
        cp = CurriculumParser(repo)
        for p in repo.list_programs():
            courses = cp.parse_for_program(p.code)
            repo.replace_courses(p.code, courses)
        print("Синхронизация завершена.")

    # общий ретривер
    ret = Retriever(repo)
    ret.build()

    if args.bot:
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            print("TELEGRAM_TOKEN не задан")
            sys.exit(1)
        bot = TelegramBot(token, repo, ret)
        bot.run()

    if args.cli:
        from dialog import UserState, WELCOME, map_background
        from qa import QAService
        from recommender import ElectiveRecommender

        qa = QAService(repo, ret)
        reco = ElectiveRecommender()
        st = UserState()
        print(WELCOME)
        while True:
            q = input("> ").strip()
            if q in ("exit","quit"): break
            if st.program_code is None:
                if q.lower() in ("ai","ai_product"):
                    st.program_code = q.lower()
                    print("Ок. Кратко опишите бэкграунд (например: junior_ml, product_manager, backend, data_engineer, research).")
                else:
                    print("Введите ai или ai_product.")
                continue
            if st.background_key is None:
                st.background_key = map_background(q) or q.lower()
                print("Принято. Спросите что-нибудь по обучению или введите :reco для рекомендаций.")
                continue
            if q == ":reco":
                courses = repo.list_courses(st.program_code)
                recs = reco.recommend(courses, st.background_key, limit=6)
                for c in recs:
                    print(f"- {c.name} (сем {c.semester or '—'}, теги: {', '.join(c.tags) or '—'})")
                continue
            print(qa.answer(st.program_code, q))

if __name__ == "__main__":
    main()