from sqlmodel import create_engine, Session


DATABASE_URL = "postgresql://postgres:123user@localhost:5432/my_api"

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session