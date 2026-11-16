import pytest
from pydantic import ValidationError

from lead_schemas import LeadQualification, LeadQualificationBatch


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


def test_valid_batch_qualification():

    data = {
        "results": [
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
                "reason": "Interested in CRM integration.",
                "needs_review": False
            }
        ]
    }

    result = LeadQualificationBatch.model_validate(data)

    assert len(result.results) == 2
    assert result.results[0].lead_id == "L001"
    assert result.results[1].lead_id == "L002"


def test_empty_batch_rejected():

    data = {
        "results": []
    }

    with pytest.raises(ValidationError):
        LeadQualificationBatch.model_validate(data)


def test_missing_lead_id_rejected():

    data = {
        "results": [
            {
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "Test reason",
                "needs_review": False
            }
        ]
    }

    with pytest.raises(ValidationError):
        LeadQualificationBatch.model_validate(data)


def test_invalid_batch_urgency_rejected():

    data = {
        "results": [
            {
                "lead_id": "L001",
                "service_interest": "marketing_automation",
                "urgency": "critical",
                "reason": "Test reason",
                "needs_review": False
            }
        ]
    }

    with pytest.raises(ValidationError):
        LeadQualificationBatch.model_validate(data)


def test_extra_field_in_batch_rejected():

    data = {
        "results": [
            {
                "lead_id": "L001",
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "Test reason",
                "needs_review": False,
                "unexpected_field": "not allowed"
            }
        ]
    }

    with pytest.raises(ValidationError):
        LeadQualificationBatch.model_validate(data)

def test_duplicate_lead_ids_rejected():

    data = {
        "results": [
            {
                "lead_id": "L001",
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "First lead",
                "needs_review": False
            },
            {
                "lead_id": "L001",
                "service_interest": "crm_integration",
                "urgency": "medium",
                "reason": "Second lead",
                "needs_review": False
            }
        ]
    }

    with pytest.raises(ValidationError):
        LeadQualificationBatch.model_validate(data)