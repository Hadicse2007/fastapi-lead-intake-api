
import pytest

import httpx2

import json

from types import SimpleNamespace

import qualify_lead as qualification_module

from lead_schemas import (LeadQualification, LeadQualificationBatch)


# Fake OpenAI Responses API
class FakeResponses:

    def __init__(self, parsed_result):
        self.parsed_result = parsed_result
        self.calls = []

    def parse(self, **kwargs):

        self.calls.append(kwargs)

        return SimpleNamespace(
            output_parsed=self.parsed_result
        )


# Fake OpenAI Client
class FakeClient:

    def __init__(self, parsed_result):

        self.responses = FakeResponses(parsed_result)


# Sample input leads
def sample_leads():

    return [
        {
            "lead_id": "L001",
            "message": "I urgently need marketing automation."
        },
        {
            "lead_id": "L002",
            "message": "I need CRM integration."
        }
    ]


# Fake valid AI output
def valid_batch_result():

    return LeadQualificationBatch(
        results=[
            {
                "lead_id": "L001",
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "Urgent automation requirement.",
                "needs_review": False
            },
            {
                "lead_id": "L002",
                "service_interest": "crm_integration",
                "urgency": "medium",
                "reason": "CRM integration requirement.",
                "needs_review": False
            }
        ]
    )


# Test 1: Successful batch qualification
def test_successful_batch_qualification(monkeypatch):

    expected_result = valid_batch_result()

    fake_client = FakeClient(expected_result)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    result = qualification_module.qualify_multiple_leads(
        sample_leads()
    )

    assert result == expected_result

    assert len(fake_client.responses.calls) == 1

    call = fake_client.responses.calls[0]

    assert call["text_format"] is LeadQualificationBatch

    assert '"lead_id": "L001"' in call["input"][1]["content"]


# Test 2: Empty input rejected
def test_empty_input_rejected(monkeypatch):

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: pytest.fail("API should not be called")
    )

    with pytest.raises(ValueError):

        qualification_module.qualify_multiple_leads([])


# Test 3: Duplicate input IDs rejected
def test_duplicate_input_ids_rejected(monkeypatch):

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: pytest.fail("API should not be called")
    )

    leads = [
        {
            "lead_id": "L001",
            "message": "First lead"
        },
        {
            "lead_id": "L001",
            "message": "Second lead"
        }
    ]

    with pytest.raises(ValueError, match="Duplicate"):

        qualification_module.qualify_multiple_leads(leads)


# Test 4: Empty message rejected
def test_empty_message_rejected(monkeypatch):

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: pytest.fail("API should not be called")
    )

    leads = [
        {
            "lead_id": "L001",
            "message": "   "
        }
    ]

    with pytest.raises(ValueError):

        qualification_module.qualify_multiple_leads(leads)


# Test 5: AI returns no structured output
def test_empty_ai_response_rejected(monkeypatch):

    fake_client = FakeClient(None)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    with pytest.raises(RuntimeError, match="No structured batch output"):

        qualification_module.qualify_multiple_leads(
            sample_leads()
        )


# Test 6: AI returns incorrect lead IDs
def test_incorrect_ai_lead_ids_rejected(monkeypatch):

    wrong_result = LeadQualificationBatch(
        results=[
            {
                "lead_id": "L999",
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "Test result.",
                "needs_review": False
            }
        ]
    )

    fake_client = FakeClient(wrong_result)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    with pytest.raises(RuntimeError, match="does not match"):

        qualification_module.qualify_multiple_leads(
            sample_leads()
        )


# Test 7: OpenAI API key is required
def test_missing_openai_api_key(monkeypatch):

    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False
    )

    with pytest.raises(
        RuntimeError,
        match="OPENAI_API_KEY is not configured"
    ):

        qualification_module.get_openai_client()



# Fake API error response
class RaisingResponses:

    def __init__(self, error):
        self.error = error

    def parse(self, **kwargs):
        raise self.error


class FakeErrorClient:

    def __init__(self, error):
        self.responses = RaisingResponses(error)


# Helper function for testing error handling
def assert_api_error_translated(
    monkeypatch,
    error,
    expected_message
):

    fake_client = FakeErrorClient(error)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    with pytest.raises(RuntimeError) as exc_info:

        qualification_module.call_openai_parse(
            model="test-model",
            input="Test message"
        )

    assert str(exc_info.value) == expected_message

    # Original error must remain available
    assert exc_info.value.__cause__ is error


# Create fake HTTP request
def create_fake_request():

    return httpx2.Request(
        "POST",
        "https://api.openai.com/v1/responses"
    )


# Create fake HTTP response
def create_fake_response(status_code):

    request = create_fake_request()

    return httpx2.Response(
        status_code=status_code,
        request=request
    )


# Test 1: Timeout error
def test_timeout_error_handling(monkeypatch):

    error = qualification_module.APITimeoutError(
        request=create_fake_request()
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "OpenAI request timed out after retries."
    )


# Test 2: Rate limit error
def test_rate_limit_error_handling(monkeypatch):

    error = qualification_module.RateLimitError(
        "Rate limit reached",
        response=create_fake_response(429),
        body=None
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "OpenAI rate limit reached. Please try again later."
    )


# Test 3: Authentication error
def test_authentication_error_handling(monkeypatch):

    error = qualification_module.AuthenticationError(
        "Authentication failed",
        response=create_fake_response(401),
        body=None
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "OpenAI authentication failed. Check your API key."
    )


# Test 4: Connection error
def test_connection_error_handling(monkeypatch):

    error = qualification_module.APIConnectionError(
        message="Connection failed",
        request=create_fake_request()
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "Could not connect to OpenAI. Check your internet connection."
    )


# Test 5: Server error
def test_server_error_handling(monkeypatch):

    error = qualification_module.APIStatusError(
        "Server unavailable",
        response=create_fake_response(503),
        body=None
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "OpenAI API returned HTTP 503."
    )


# Test 6: Generic API error
def test_generic_api_error_handling(monkeypatch):

    error = qualification_module.APIError(
        "Unexpected API error",
        create_fake_request(),
        body=None
    )

    assert_api_error_translated(
        monkeypatch,
        error,
        "An OpenAI API error occurred."
    )


# Test 1: Successful request logging
def test_successful_request_logging(monkeypatch, caplog):

    expected_result = valid_batch_result()

    fake_client = FakeClient(expected_result)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    with caplog.at_level(
        "INFO",
        logger=qualification_module.__name__
    ):

        response = qualification_module.call_openai_parse(
            model="test-model",
            input="PRIVATE_CUSTOMER_MESSAGE"
        )

    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == qualification_module.__name__
    ]

    assert response.output_parsed == expected_result

    assert events[0]["event"] == "openai_request_started"
    assert events[1]["event"] == "openai_request_completed"

    assert events[0]["request_id"] == events[1]["request_id"]

    assert isinstance(events[1]["duration_ms"], (int, float))
    assert events[1]["duration_ms"] >= 0

    # Customer message must not appear in logs
    assert "PRIVATE_CUSTOMER_MESSAGE" not in caplog.text


# Test 2: Failed request logging
def test_failed_request_logging(monkeypatch, caplog):

    error = qualification_module.APITimeoutError(
        request=create_fake_request()
    )

    fake_client = FakeErrorClient(error)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    with caplog.at_level(
        "INFO",
        logger=qualification_module.__name__
    ):

        with pytest.raises(RuntimeError):

            qualification_module.call_openai_parse(
                model="test-model",
                input="Test message"
            )

    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == qualification_module.__name__
    ]

    assert events[0]["event"] == "openai_request_started"
    assert events[1]["event"] == "openai_request_failed"

    assert events[1]["error_type"] == "timeout"

    assert events[0]["request_id"] == events[1]["request_id"]

    assert isinstance(events[1]["duration_ms"], (int, float))
    assert events[1]["duration_ms"] >= 0


# Test 1: Successful single lead qualification
def test_successful_single_lead_qualification(monkeypatch):

    expected_result = LeadQualification(
        service_interest="crm_integration",
        urgency="high",
        reason="The lead urgently needs CRM integration.",
        needs_review=False
    )

    fake_client = FakeClient(expected_result)

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: fake_client
    )

    result = qualification_module.qualify_lead(
        "  I urgently need CRM integration.  "
    )

    assert result == expected_result

    assert len(fake_client.responses.calls) == 1

    call = fake_client.responses.calls[0]

    assert call["text_format"] is LeadQualification

    assert (
        call["input"][1]["content"]
        == "I urgently need CRM integration."
    )


# Test 2: Empty or whitespace-only messages rejected
@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "\n\t"
    ]
)
def test_empty_single_lead_message_rejected(
    monkeypatch,
    message
):

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: pytest.fail("API should not be called")
    )

    with pytest.raises(
        ValueError,
        match="Lead message cannot be empty"
    ):

        qualification_module.qualify_lead(message)


# Test 3: Invalid input types rejected
@pytest.mark.parametrize(
    "message",
    [
        None,
        123,
        [],
        {}
    ]
)
def test_invalid_single_lead_input_type_rejected(
    monkeypatch,
    message
):

    monkeypatch.setattr(
        qualification_module,
        "get_openai_client",
        lambda: pytest.fail("API should not be called")
    )

    with pytest.raises(
        TypeError,
        match="Lead message must be a string"
    ):

        qualification_module.qualify_lead(message)