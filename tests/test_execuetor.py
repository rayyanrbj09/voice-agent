import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import Customer, User
from app.tools.executor import ToolExecutionError, execute_tool


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


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_test_user(db, email):
    user = User(
        email=email,
        hashed_password="test_hash",
        full_name="Test User",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_customer(db, user_id):
    customer = Customer(
        name="Rahul Sharma",
        email="rahul@example.com",
        phone="9876543210",
        company="Acme",
        created_by_user_id=user_id,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def test_execute_search_customer():
    db = TestingSessionLocal()

    try:
        user = create_test_user(db, "user@example.com")
        create_test_customer(db, user.id)

        results = execute_tool(
            db=db,
            user_id=user.id,
            tool_name="search_customer",
            arguments={
                "query": "Rahul",
            },
        )

        assert len(results) == 1
        assert results[0].name == "Rahul Sharma"

    finally:
        db.close()


def test_unknown_tool_is_rejected():
    db = TestingSessionLocal()

    try:
        user = create_test_user(db, "user@example.com")

        with pytest.raises(ToolExecutionError, match="Unknown tool"):
            execute_tool(
                db=db,
                user_id=user.id,
                tool_name="does_not_exist",
                arguments={},
            )

    finally:
        db.close()


def test_invalid_arguments_are_rejected():
    db = TestingSessionLocal()

    try:
        user = create_test_user(db, "user@example.com")

        with pytest.raises(
            ToolExecutionError,
            match="Invalid arguments",
        ):
            execute_tool(
                db=db,
                user_id=user.id,
                tool_name="search_customer",
                arguments={
                    "wrong_argument": "Rahul",
                },
            )

    finally:
        db.close()


def test_tool_cannot_choose_user_id_from_arguments():
    db = TestingSessionLocal()

    try:
        user = create_test_user(db, "user@example.com")
        create_test_customer(db, user.id)

        with pytest.raises(
            ToolExecutionError,
            match="Invalid arguments",
        ):
            execute_tool(
                db=db,
                user_id=user.id,
                tool_name="search_customer",
                arguments={
                    "query": "Rahul",
                    "user_id": 999,
                },
            )

    finally:
        db.close()