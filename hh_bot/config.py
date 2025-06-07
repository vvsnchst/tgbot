from dataclasses import dataclass
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# Создаем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent

@dataclass
class Config:
    BOT_TOKEN: str = ""
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.sqlite3")
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    RESUMES_DIR: str = "resumes"
    VACANCIES_DIR: str = "vacancies"

    def __post_init__(self):
        # Создаем директории для файлов, если они не существуют
        os.makedirs(self.VACANCIES_DIR, exist_ok=True)
        os.makedirs(self.RESUMES_DIR, exist_ok=True)

config = Config() 
