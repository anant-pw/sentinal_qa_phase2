from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

class DBClient:
    def __init__(self):
        # sqlite:///./sentinel.db
        url = os.getenv("DATABASE_URL")
        # 'check_same_thread' is required ONLY for SQLite
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()