import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import jwt
import bcrypt

from backend.app.core.config import settings
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from backend.app.models.user import UserModel
from backend.app.repositories.user_repository import UserRepository
from sqlalchemy.orm import sessionmaker


def test_scenario_01_user_registration(client: TestClient, db_session: Session):
    """Scenario 1: User Registration creates a persistent UserModel with hashed password and timestamps."""
    reg_payload = {
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.com",
        "password": "ValidPassword#2026"
    }

    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["success"] is True
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Aarav Sharma"
    assert data["user"]["email"] == "aarav.sharma@example.com"
    assert data["user"]["initials"] == "AS"
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

    # Verify directly in SQLite database
    db_user = db_session.query(UserModel).filter_by(email="aarav.sharma@example.com").first()
    assert db_user is not None
    assert db_user.full_name == "Aarav Sharma"
    assert db_user.hashed_password != reg_payload["password"]
    assert db_user.is_active is True
    assert db_user.created_at is not None
    assert db_user.updated_at is not None


def test_scenario_02_duplicate_registration_rejection(client: TestClient):
    """Scenario 2: Duplicate registration with an existing email returns HTTP 409 Conflict."""
    payload = {
        "name": "Priya Patel",
        "email": "priya.patel@example.com",
        "password": "StrongPassword!456"
    }

    # First registration: succeeds
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email (case-insensitive): rejected
    payload_dup = {
        "name": "Priya Patel Duplicate",
        "email": "PRIYA.PATEL@example.com",
        "password": "AnotherPassword!789"
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 409
    data = res2.json()
    assert "already exists" in data["detail"].lower()


def test_scenario_03_password_hashing(db_session: Session):
    """Scenario 3: Password hashing uses bcrypt; plain password does not match stored hash; bcrypt.checkpw verifies."""
    plaintext = "SensitiveSecretPassword#999"
    hashed = hash_password(plaintext)

    assert hashed != plaintext
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # bcrypt.checkpw verification
    assert verify_password(plaintext, hashed) is True
    assert verify_password("WrongPassword#000", hashed) is False

    # Unique salts produce different hashes for the same password
    hashed2 = hash_password(plaintext)
    assert hashed != hashed2
    assert verify_password(plaintext, hashed2) is True


def test_scenario_04_user_login_success(client: TestClient):
    """Scenario 4: Valid login credentials return HTTP 200 with a valid signed JWT bearer token and user metadata."""
    email = "vikram.singh@example.com"
    password = "SecurePassword#2026"

    # Register user
    client.post("/api/v1/auth/register", json={
        "name": "Vikram Singh",
        "email": email,
        "password": password
    })

    # Log in
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    data = login_res.json()

    assert data["success"] is True
    token = data["token"]
    assert token is not None
    assert len(token.split(".")) == 3  # Standard JWT format: header.payload.signature

    # Verify JWT payload claims
    decoded = decode_access_token(token)
    assert decoded["email"] == email
    assert "sub" in decoded
    assert "exp" in decoded

    # Verify user profile in response
    user_info = data["user"]
    assert user_info["email"] == email
    assert user_info["name"] == "Vikram Singh"
    assert "hashed_password" not in user_info
    assert "password" not in user_info


def test_scenario_05_login_failure_wrong_password(client: TestClient):
    """Scenario 5: Incorrect password returns HTTP 401 Unauthorized with generic error preventing enumeration."""
    email = "ananya.rao@example.com"
    password = "CorrectPassword#123"

    client.post("/api/v1/auth/register", json={
        "name": "Ananya Rao",
        "email": email,
        "password": password
    })

    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword#999"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_scenario_06_login_failure_non_existent_user(client: TestClient):
    """Scenario 6: Unknown email returns HTTP 401 Unauthorized with the identical generic message."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent.investor@example.com",
        "password": "SomeArbitraryPassword!123"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_scenario_07_token_authenticity_tampered_or_unsigned(client: TestClient):
    """Scenario 7: Tampered or forged JWT tokens passed to /auth/me return HTTP 401 Unauthorized."""
    # Token signed with an arbitrary bogus secret
    bogus_token = jwt.encode(
        {"sub": "fake-user-id", "email": "hacker@evil.com", "exp": 9999999999},
        "completely-wrong-secret-key-1234567890",
        algorithm="HS256"
    )

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bogus_token}"})
    assert res.status_code == 401
    assert "token" in res.json()["detail"].lower() or "not authenticated" in res.json()["detail"].lower()

    # Plain malformed string
    res_malformed = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-even-a-jwt"})
    assert res_malformed.status_code == 401


def test_scenario_08_token_expiration(client: TestClient):
    """Scenario 8: Expired JWT tokens passed to /auth/me return HTTP 401 Unauthorized."""
    # Generate expired token (-10 seconds)
    expired_token = create_access_token(
        user_id="any-user-id",
        email="test@example.com",
        expires_delta=timedelta(seconds=-10)
    )

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_scenario_09_token_format_migration_rejects_legacy(client: TestClient):
    """Scenario 9: Legacy ft_tok_... and syn_tok_... tokens are strictly rejected with HTTP 401."""
    legacy_tokens = [
        "ft_tok_9b7c8d9e0f1a2b3c",
        "ft_tok_1234567890abcdef",
        "syn_tok_abcdef1234567890"
    ]

    for legacy in legacy_tokens:
        res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {legacy}"})
        assert res.status_code == 401
        assert "invalid" in res.json()["detail"].lower() or "token" in res.json()["detail"].lower()


def test_scenario_10_current_user_profile_real_user(client: TestClient):
    """Scenario 10: /auth/me returns the authenticated user's real DB record, eliminating hardcoded 'Nakul Verma'."""
    email = "kavita.nair@example.com"
    name = "Kavita Nair"
    password = "KavitaPassword#2026"

    reg_res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })
    token = reg_res.json()["token"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()

    assert user_data["name"] == name
    assert user_data["email"] == email
    assert user_data["initials"] == "KN"
    assert user_data["isActive"] is True
    assert "stats" in user_data


def test_scenario_11_user_data_isolation(client: TestClient):
    """Scenario 11: Users cannot access or delete resources owned by other users."""
    # User A registers & logs in
    res_a = client.post("/api/v1/auth/register", json={
        "name": "User Alpha",
        "email": "alpha@example.com",
        "password": "AlphaPassword#123"
    })
    token_a = res_a.json()["token"]

    # User B registers & logs in
    res_b = client.post("/api/v1/auth/register", json={
        "name": "User Beta",
        "email": "beta@example.com",
        "password": "BetaPassword#123"
    })
    token_b = res_b.json()["token"]

    # User A submits a claim
    claim_payload = {
        "original_claim": "Alpha Corporation quarterly earnings will beat guidance by 25%.",
        "ticker": "ALPHA"
    }
    claim_res = client.post(
        "/api/v1/claims",
        json=claim_payload,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert claim_res.status_code == 201
    claim_id = claim_res.json()["id"]

    # User A can access their own claim
    get_a = client.get(f"/api/v1/claims/{claim_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200

    # User B attempts to access User A's claim: HTTP 403 Forbidden
    get_b = client.get(f"/api/v1/claims/{claim_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 403
    assert "access denied" in get_b.json()["detail"].lower()

    # User B attempts to delete User A's claim: HTTP 403 Forbidden
    del_b = client.delete(f"/api/v1/claims/{claim_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 403

    # User A can delete their own claim: HTTP 204
    del_a = client.delete(f"/api/v1/claims/{claim_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a.status_code == 204


def test_scenario_12_logout_invalidation(client: TestClient):
    """Scenario 12: /auth/logout succeeds and instructs client to discard the session token."""
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "discard" in data["message"].lower() or "logged out" in data["message"].lower()


def test_scenario_13_password_validation_rejections(client: TestClient):
    """Scenario 13: Passwords shorter than 6 characters or empty passwords are rejected at registration."""
    # Too short (< 6 characters)
    res_short = client.post("/api/v1/auth/register", json={
        "name": "Short Password User",
        "email": "short@example.com",
        "password": "123"
    })
    assert res_short.status_code in [400, 422]

    # Empty password
    res_empty = client.post("/api/v1/auth/register", json={
        "name": "Empty Password User",
        "email": "empty@example.com",
        "password": ""
    })
    assert res_empty.status_code in [400, 422]


def test_scenario_14_database_persistence_across_sessions(db_session: Session):
    """Scenario 14: User created in one database session persists and is queryable in a fresh session."""
    email = "persistent.analyst@example.com"
    name = "Persistent Analyst"
    hashed_pw = hash_password("PersistentPass#2026")

    engine = db_session.get_bind()
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Session 1: Create user
    session1 = LocalSession()
    try:
        repo1 = UserRepository(session1)
        created_user = repo1.create(full_name=name, email=email, hashed_password=hashed_pw)
        user_id = created_user.id
    finally:
        session1.close()

    # Session 2: Query user in a completely fresh session
    session2 = LocalSession()
    try:
        repo2 = UserRepository(session2)
        retrieved_user = repo2.get_by_id(user_id)
        assert retrieved_user is not None
        assert retrieved_user.email == email
        assert retrieved_user.full_name == name
        assert verify_password("PersistentPass#2026", retrieved_user.hashed_password) is True
    finally:
        session2.close()


def test_scenario_15_inactive_user_handling(client: TestClient, db_session: Session):
    """Scenario 15: An inactive user (is_active=False) cannot log in and existing tokens are rejected."""
    email = "inactive.user@example.com"
    password = "InactivePass#2026"

    # Register user
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Inactive User",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201
    active_token = reg_res.json()["token"]

    # Deactivate user in database
    db_user = db_session.query(UserModel).filter_by(email=email).first()
    assert db_user is not None
    db_user.is_active = False
    db_session.commit()

    # Attempt to log in with valid credentials: rejected
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 401
    assert "inactive" in login_res.json()["detail"].lower()

    # Attempt to access /auth/me with existing token: rejected
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {active_token}"})
    assert me_res.status_code == 401
    assert "inactive" in me_res.json()["detail"].lower()
