import os

# শুধু clean test environment-এর জন্য fallback key।
# project-এ .env থাকলে main.py সেখান থেকেই API_KEY নেবে।
os.environ.setdefault("API_KEY", "test-secret-key")


from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import requests

from main import app, APIkey, get_mock_company_info


client = TestClient(app)


# ---------------------------------------------------------
# 1. Health endpoint test
# ---------------------------------------------------------
def test_health_check():

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------
# 2. Valid lead / Happy path test
# ---------------------------------------------------------
def test_valid_lead():

    lead_data = {
        "event_id": "evt_003",
        "name": "Rahim",
        "email": "rahim@gmail.com",
        "phone": "01700000000",
        "message": "Need automation service",
    }

    fake_company_info = {
        "id": 1,
        "name": "Demo Company",
        "email": "demo@example.com",
        "phone": "123456",
    }

    with patch(
        "main.get_mock_company_info",
        return_value=fake_company_info,
    ):

        response = client.post(
            "/leads",
            json=lead_data,
            headers={
                "X-API-Key": APIkey
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "received"
    assert "request_id" in data
    assert data["company_info"] == fake_company_info


# ---------------------------------------------------------
# 3. Missing required field test
# ---------------------------------------------------------
def test_missing_message():

    lead_data = {
        "event_id": "evt_004",
        "name": "Karim",
        "email": "karim@gmail.com",
    }

    response = client.post(
        "/leads",
        json=lead_data,
        headers={
            "X-API-Key": APIkey
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# 4. Invalid email test
# ---------------------------------------------------------
def test_invalid_email():

    lead_data = {
        "event_id": "evt_005",
        "name": "Nadia",
        "email": "not-an-email",
        "message": "Need CRM automation",
    }

    response = client.post(
        "/leads",
        json=lead_data,
        headers={
            "X-API-Key": APIkey
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# 5. Missing API key test
# ---------------------------------------------------------
def test_missing_api_key():

    lead_data = {
        "event_id": "evt_006",
        "name": "Hasan",
        "email": "hasan@gmail.com",
        "message": "Need workflow automation",
    }

    response = client.post(
        "/leads",
        json=lead_data,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"]["message"] == "Invalid API Key"
    assert "request_id" in data["detail"]


# ---------------------------------------------------------
# 6. Wrong API key test
# ---------------------------------------------------------
def test_wrong_api_key():

    lead_data = {
        "event_id": "evt_007",
        "name": "Mina",
        "email": "mina@gmail.com",
        "message": "Need reporting automation",
    }

    response = client.post(
        "/leads",
        json=lead_data,
        headers={
            "X-API-Key": "wrong-key"
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"]["message"] == "Invalid API Key"


# ---------------------------------------------------------
# 7. External API timeout + retry test
# ---------------------------------------------------------
def test_upstream_timeout_after_retries():

    with patch(
        "main.requests.get",
        side_effect=requests.exceptions.Timeout,
    ) as mock_get:

        try:

            get_mock_company_info(
                "req-timeout-001"
            )

            assert False, "Expected HTTPException was not raised"

        except HTTPException as exc:

            assert exc.status_code == 504

            assert (
                exc.detail["message"]
                == "Upstream service timed out"
            )

    assert mock_get.call_count == 3


# ---------------------------------------------------------
# 8. External API 500 + retry test
# ---------------------------------------------------------
def test_upstream_500_after_retries():

    fake_response = Mock()

    fake_response.status_code = 500

    with patch(
        "main.requests.get",
        return_value=fake_response,
    ) as mock_get:

        try:

            get_mock_company_info(
                "req-500-001"
            )

            assert False, "Expected HTTPException was not raised"

        except HTTPException as exc:

            assert exc.status_code == 502

            assert (
                exc.detail["message"]
                == "Upstream service failed"
            )

    assert mock_get.call_count == 3