from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.tools.customer import search_customer


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register_and_login(email: str):
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    return response.json()["access_token"]


def test_search_customer():
    token = register_and_login("user@example.com")

    client.post(
        "/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "phone": "9876543210",
            "company": "Acme",
        },
    )

    db = TestingSessionLocal()

    try:
        results = search_customer(
            db=db,
            user_id=1,
            query="Rahul",
        )

        assert len(results) == 1
        assert results[0].name == "Rahul Sharma"

    finally:
        db.close()


def test_search_customer_is_user_scoped():
    token_a = register_and_login("user_a@example.com")

    client.post(
        "/customers",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "company": "Acme",
        },
    )

    token_b = register_and_login("user_b@example.com")

    db = TestingSessionLocal()

    try:
        results = search_customer(
            db=db,
            user_id=2,
            query="Rahul",
        )

        assert results == []

    finally:
        db.close()