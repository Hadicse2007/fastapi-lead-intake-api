import pytest
from pydantic import ValidationError

from lead_schemas import LeadQualification


def test_valid_lead_qualification():

    data = {
        "service_interest": "marketing_automation",
        "urgency": "high",
        "reason": "The lead needs automation urgently.",
        "needs_review": False
    }

    result = LeadQualification.model_validate(data)

    assert result.service_interest == "marketing_automation"
    assert result.urgency == "high"
    assert result.needs_review is False


def test_invalid_service_interest():

    data = {
        "service_interest": "web_design",
        "urgency": "high",
        "reason": "Test reason",
        "needs_review": False
    }

    with pytest.raises(ValidationError):
        LeadQualification.model_validate(data)


def test_invalid_urgency():

    data = {
        "service_interest": "marketing_automation",
        "urgency": "super_urgent",
        "reason": "Test reason",
        "needs_review": False
    }

    with pytest.raises(ValidationError):
        LeadQualification.model_validate(data)


def test_missing_required_field():

    data = {
        "service_interest": "marketing_automation",
        "urgency": "high",
        "reason": "Test reason"
    }

    with pytest.raises(ValidationError):
        LeadQualification.model_validate(data)


def test_extra_field_rejected():

    data = {
        "service_interest": "marketing_automation",
        "urgency": "high",
        "reason": "Test reason",
        "needs_review": False,
        "customer_password": "123456"
    }

    with pytest.raises(ValidationError):
        LeadQualification.model_validate(data)