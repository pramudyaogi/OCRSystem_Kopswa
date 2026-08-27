from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import BASE_DIR
import os

# Menentukan lokasi file SQLite lokal di folder database/ (di root proyek)
DB_PATH = BASE_DIR.parent / "database" / "app.db"

# Pastikan folder database ada
os.makedirs(DB_PATH.parent, exist_ok=True)

# Format URL koneksi untuk SQLAlchemy
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Parameter check_same_thread=False diperlukan untuk SQLite + FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Pembuatan sesi koneksi ke DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk membuat model tabel
Base = declarative_base()

# Dependency injektor untuk mengambil sesi DB di setiap API endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
