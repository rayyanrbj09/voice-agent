from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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

def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data

def test_duplicate_email():
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "Test User",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"

def test_invalid_email():
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422

def test_short_password():
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "password": "123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422

def test_login_success():
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert len(data["access_token"]) > 20


def test_login_wrong_password():
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

def test_login_nonexistent_user():
    response = client.post(
        "/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401

def test_me_without_token():
    response = client.get("/auth/me")

    assert response.status_code == 401

def test_me_with_valid_token():
    client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "full_name": "Me User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "me@example.com",
            "password": "password123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"
    assert data["is_active"] is True

def test_me_with_invalid_token():
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer this-is-not-a-valid-token",
        },
    )

    assert response.status_code == 401


def test_me_with_modified_token():
    client.post(
        "/auth/register",
        json={
            "email": "modified@example.com",
            "password": "password123",
            "full_name": "Modified Token",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "modified@example.com",
            "password": "password123",
        },
    )

    token = login_response.json()["access_token"]

    modified_token = token[:-5] + "xxxxx"

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {modified_token}",
        },
    )

    assert response.status_code == 401