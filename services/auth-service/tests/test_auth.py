import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    response = await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    response = await client.post(
        "/login",
        json={"email": "test@test.com", "password": "test1234"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    response = await client.post(
        "/login",
        json={"email": "test@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/login",
        json={"email": "nobody@test.com", "password": "test1234"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_valid_token(client):
    register_response = await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    token = register_response.json()["access_token"]
    response = await client.post(f"/verify?token={token}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@test.com"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_verify_invalid_token(client):
    response = await client.post("/verify?token=invalidtoken")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_valid_token(client):
    register_response = await client.post(
        "/register",
        json={"email": "test@test.com", "password": "test1234"},
    )
    token = register_response.json()["access_token"]
    response = await client.get(f"/me?token={token}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@test.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    response = await client.get("/me?token=invalidtoken")
    assert response.status_code == 401
