from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 

SQLALCHEMY_DATABASE_URL = "postgresql://tecteria_db_user:S2DzqaDIy6CGqCm6NPpz0TKlgplKeB45@dpg-curja99u0jms73bv2epg-a.oregon-postgres.render.com/tecteria_db"


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

metadata = MetaData()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()