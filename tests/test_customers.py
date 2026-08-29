from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db


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


def register_user(email: str, password: str = "password123"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    return response.json()


def login_user(email: str, password: str = "password123"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_customer(token: str, email: str = "customer@example.com"):
    return client.post(
        "/customers",
        headers=auth_headers(token),
        json={
            "name": "Test Customer",
            "email": email,
            "phone": "9876543210",
            "company": "Test Company",
        },
    )


def test_create_customer():
    register_user("user@example.com")
    token = login_user("user@example.com")

    response = create_customer(token)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["phone"] == "9876543210"
    assert data["company"] == "Test Company"
    assert "id" in data
    assert "created_by_user_id" in data
    assert "created_at" in data


def test_list_customers():
    register_user("user@example.com")
    token = login_user("user@example.com")

    create_customer(token)

    response = client.get(
        "/customers",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "customer@example.com"


def test_get_customer():
    register_user("user@example.com")
    token = login_user("user@example.com")

    create_response = create_customer(token)
    customer_id = create_response.json()["id"]

    response = client.get(
        f"/customers/{customer_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == customer_id


def test_update_customer():
    register_user("user@example.com")
    token = login_user("user@example.com")

    create_response = create_customer(token)
    customer_id = create_response.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}",
        headers=auth_headers(token),
        json={
            "phone": "9999999999",
            "company": "Updated Company",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["phone"] == "9999999999"
    assert data["company"] == "Updated Company"
    assert data["name"] == "Test Customer"


def test_delete_customer():
    register_user("user@example.com")
    token = login_user("user@example.com")

    create_response = create_customer(token)
    customer_id = create_response.json()["id"]

    response = client.delete(
        f"/customers/{customer_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/customers/{customer_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


def test_customers_require_authentication():
    response = client.get("/customers")

    assert response.status_code == 401


def test_user_cannot_access_another_users_customer():
    register_user("user_a@example.com")
    token_a = login_user("user_a@example.com")

    create_response = create_customer(
        token_a,
        email="customer_a@example.com",
    )

    customer_id = create_response.json()["id"]

    register_user("user_b@example.com")
    token_b = login_user("user_b@example.com")

    response = client.get(
        f"/customers/{customer_id}",
        headers=auth_headers(token_b),
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_customer():
    register_user("user_a@example.com")
    token_a = login_user("user_a@example.com")

    create_response = create_customer(
        token_a,
        email="customer_a@example.com",
    )

    customer_id = create_response.json()["id"]

    register_user("user_b@example.com")
    token_b = login_user("user_b@example.com")

    response = client.patch(
        f"/customers/{customer_id}",
        headers=auth_headers(token_b),
        json={
            "name": "Hacked Customer",
        },
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_customer():
    register_user("user_a@example.com")
    token_a = login_user("user_a@example.com")

    create_response = create_customer(
        token_a,
        email="customer_a@example.com",
    )

    customer_id = create_response.json()["id"]

    register_user("user_b@example.com")
    token_b = login_user("user_b@example.com")

    response = client.delete(
        f"/customers/{customer_id}",
        headers=auth_headers(token_b),
    )

    assert response.status_code == 404