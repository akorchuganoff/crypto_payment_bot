from sqlalchemy import create_engine, Column, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Создаем экземпляр базы данных
engine = create_engine('sqlite:///cryptobot.db', echo=True)
Base = declarative_base()

# Определяем модель пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    ton_balance = Column(Float)
    bnb_balance = Column(Float)
    lt_balance = Column(Float)
    risk_amount = Column(Float)

# Создаем таблицу, если она еще не существует
Base.metadata.create_all(engine)

# Создаем сессию
Session = sessionmaker(bind=engine)
session = Session()
