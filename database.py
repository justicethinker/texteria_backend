from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 

SQLALCHEMY_DATABASE_URL = "postgresql://medinnovate_user:thethinker@localhost:5432/medinnovate_db"


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

metadata = MetaData()