from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pymysql

pymysql.install_as_MySQLdb()

# MySQL 연결 설정 (본인의 DB 정보로 변경)
DATABASE_URL = "mysql+pymysql://root:flyaidopamin@localhost:3306/my_app_db"

# SQLAlchemy 엔진 및 세션 설정
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()