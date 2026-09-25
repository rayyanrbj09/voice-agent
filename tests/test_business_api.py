from fastapi.testclient import TestClient

from app.main import app
from app.tools.appointments import book_appointment
from app.tools.orders import create_order as tool_create_order
from app.tools.support import create_support_ticket as tool_create_ticket
from conftest import TestingSessionLocal

client = TestClient(app)


def register_user(email: str, password: str = "password123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


def login_user(email: str, password: str = "password123") -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def create_customer(token: str, email: str = "cust@example.com") -> dict:
    response = client.post(
        "/customers",
        headers=auth_headers(token),
        json={
            "name": "Acme Corp",
            "email": email,
            "phone": "555-1234",
            "company": "Acme Inc",
        },
    )
    assert response.status_code == 201
    return response.json()


# ============================================================================
# Appointments API Tests
# ============================================================================

def test_appointment_crud_and_user_isolation():
    register_user("user1@example.com")
    register_user("user2@example.com")
    token1 = login_user("user1@example.com")
    token2 = login_user("user2@example.com")

    cust1 = create_customer(token1, "cust1@example.com")
    cust2 = create_customer(token2, "cust2@example.com")

    # 1. Create appointment for user1's customer
    res = client.post(
        "/appointments",
        headers=auth_headers(token1),
        json={
            "customer_id": cust1["id"],
            "starts_at": "2026-11-01T14:00:00",
            "duration_minutes": 45,
            "notes": "Discuss renewal",
        },
    )
    assert res.status_code == 201
    appt1 = res.json()
    assert appt1["customer_id"] == cust1["id"]
    assert appt1["status"] == "scheduled"
    assert appt1["duration_minutes"] == 45

    # 2. Cannot create appointment for another user's customer
    res_cross = client.post(
        "/appointments",
        headers=auth_headers(token2),
        json={
            "customer_id": cust1["id"],
            "starts_at": "2026-11-01T15:00:00",
        },
    )
    assert res_cross.status_code == 404

    # 3. List appointments - user isolation
    res_list1 = client.get("/appointments", headers=auth_headers(token1))
    assert res_list1.status_code == 200
    assert len(res_list1.json()) == 1

    res_list2 = client.get("/appointments", headers=auth_headers(token2))
    assert res_list2.status_code == 200
    assert len(res_list2.json()) == 0

    # 4. Get single appointment
    res_get = client.get(f"/appointments/{appt1['id']}", headers=auth_headers(token1))
    assert res_get.status_code == 200
    assert res_get.json()["id"] == appt1["id"]

    res_get_unauth = client.get(f"/appointments/{appt1['id']}", headers=auth_headers(token2))
    assert res_get_unauth.status_code == 404

    # 5. Update appointment
    res_patch = client.patch(
        f"/appointments/{appt1['id']}",
        headers=auth_headers(token1),
        json={"notes": "Updated notes", "duration_minutes": 60},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["notes"] == "Updated notes"
    assert res_patch.json()["duration_minutes"] == 60

    # 6. Cancel appointment
    res_cancel = client.post(
        f"/appointments/{appt1['id']}/cancel",
        headers=auth_headers(token1),
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"

    # Filter by status
    res_filter = client.get("/appointments?status=cancelled", headers=auth_headers(token1))
    assert len(res_filter.json()) == 1
    res_filter_sched = client.get("/appointments?status=scheduled", headers=auth_headers(token1))
    assert len(res_filter_sched.json()) == 0

    # 7. Delete appointment
    res_del = client.delete(f"/appointments/{appt1['id']}", headers=auth_headers(token1))
    assert res_del.status_code == 204

    # Confirm deletion
    res_get_deleted = client.get(f"/appointments/{appt1['id']}", headers=auth_headers(token1))
    assert res_get_deleted.status_code == 404


# ============================================================================
# Orders API Tests
# ============================================================================

def test_orders_crud_and_conflict_handling():
    register_user("user1@example.com")
    register_user("user2@example.com")
    token1 = login_user("user1@example.com")
    token2 = login_user("user2@example.com")

    cust1 = create_customer(token1, "cust1@example.com")

    # 1. Create order
    res = client.post(
        "/orders",
        headers=auth_headers(token1),
        json={
            "customer_id": cust1["id"],
            "order_number": "ORD-1001",
            "description": "Enterprise Subscription",
            "total_amount": 499.99,
            "status": "pending",
        },
    )
    assert res.status_code == 201
    order1 = res.json()
    assert order1["order_number"] == "ORD-1001"
    assert order1["total_amount"] == 499.99

    # 2. Duplicate order_number for same user returns 409
    res_dup = client.post(
        "/orders",
        headers=auth_headers(token1),
        json={
            "customer_id": cust1["id"],
            "order_number": "ORD-1001",
            "description": "Duplicate order",
            "total_amount": 100.0,
        },
    )
    assert res_dup.status_code == 409

    # 3. List and get orders
    res_list = client.get("/orders", headers=auth_headers(token1))
    assert len(res_list.json()) == 1

    res_list_other = client.get("/orders", headers=auth_headers(token2))
    assert len(res_list_other.json()) == 0

    # 4. Update order
    res_patch = client.patch(
        f"/orders/{order1['id']}",
        headers=auth_headers(token1),
        json={"status": "completed", "total_amount": 450.0},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "completed"
    assert res_patch.json()["total_amount"] == 450.0

    # 5. Delete order
    res_del = client.delete(f"/orders/{order1['id']}", headers=auth_headers(token1))
    assert res_del.status_code == 204

    res_get = client.get(f"/orders/{order1['id']}", headers=auth_headers(token1))
    assert res_get.status_code == 404


# ============================================================================
# Support Tickets API Tests
# ============================================================================

def test_support_tickets_crud_and_status_filtering():
    register_user("user1@example.com")
    token1 = login_user("user1@example.com")
    cust1 = create_customer(token1, "cust1@example.com")

    # 1. Create support ticket
    res = client.post(
        "/support-tickets",
        headers=auth_headers(token1),
        json={
            "customer_id": cust1["id"],
            "subject": "System login issue",
            "description": "Cannot log in with SSO",
            "priority": "high",
        },
    )
    assert res.status_code == 201
    ticket = res.json()
    assert ticket["subject"] == "System login issue"
    assert ticket["priority"] == "high"
    assert ticket["status"] == "open"

    # 2. Update status and priority
    res_patch = client.patch(
        f"/support-tickets/{ticket['id']}",
        headers=auth_headers(token1),
        json={"status": "resolved", "priority": "normal"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "resolved"
    assert res_patch.json()["priority"] == "normal"

    # 3. Filtering
    res_filter = client.get("/support-tickets?status=resolved", headers=auth_headers(token1))
    assert len(res_filter.json()) == 1
    res_filter_open = client.get("/support-tickets?status=open", headers=auth_headers(token1))
    assert len(res_filter_open.json()) == 0

    # 4. Delete
    res_del = client.delete(f"/support-tickets/{ticket['id']}", headers=auth_headers(token1))
    assert res_del.status_code == 204


# ============================================================================
# Integration: Tools Write to DB and REST API Reads the Same Rows
# ============================================================================

def test_tool_calls_create_rows_visible_in_rest_api():
    register_user("user1@example.com")
    token = login_user("user1@example.com")
    cust = create_customer(token, "cust@example.com")
    user_id = cust["created_by_user_id"]

    db = TestingSessionLocal()
    try:
        # 1. Book appointment via tool
        appt = book_appointment(
            db=db,
            user_id=user_id,
            customer_id=cust["id"],
            starts_at="2026-12-01T09:00:00",
            duration_minutes=30,
            notes="Booked via agent tool",
        )
        assert appt.id is not None

        # 2. Create order via tool
        ord_rec = tool_create_order(
            db=db,
            user_id=user_id,
            customer_id=cust["id"],
            order_number="ORD-AGENT-01",
            description="Agent generated order",
            total_amount=199.99,
        )
        assert ord_rec.id is not None

        # 3. Create ticket via tool
        tkt = tool_create_ticket(
            db=db,
            user_id=user_id,
            customer_id=cust["id"],
            subject="Agent support ticket",
            description="Created by agent tool",
            priority="urgent",
        )
        assert tkt.id is not None
    finally:
        db.close()

    # Now verify REST API sees all three entities
    res_appts = client.get("/appointments", headers=auth_headers(token))
    assert res_appts.status_code == 200
    assert len(res_appts.json()) == 1
    assert res_appts.json()[0]["notes"] == "Booked via agent tool"

    res_orders = client.get("/orders", headers=auth_headers(token))
    assert res_orders.status_code == 200
    assert len(res_orders.json()) == 1
    assert res_orders.json()[0]["order_number"] == "ORD-AGENT-01"

    res_tickets = client.get("/support-tickets", headers=auth_headers(token))
    assert res_tickets.status_code == 200
    assert len(res_tickets.json()) == 1
    assert res_tickets.json()[0]["priority"] == "urgent"
