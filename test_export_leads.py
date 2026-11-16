
import csv

import pytest

from export_leads import export_leads_to_csv
from lead_schemas import LeadQualificationBatch


# Sample batch data for testing
def create_sample_batch():

    return LeadQualificationBatch(
        results=[
            {
                "lead_id": "L001",
                "service_interest": "marketing_automation",
                "urgency": "high",
                "reason": "গ্রাহকের জরুরি প্রয়োজন।",
                "needs_review": False
            },
            {
                "lead_id": "L002",
                "service_interest": "crm_integration",
                "urgency": "medium",
                "reason": "Interested in CRM integration.",
                "needs_review": True
            }
        ]
    )


# Test 1: CSV file is created with correct headers
def test_csv_file_creation(tmp_path):

    batch = create_sample_batch()

    output_file = tmp_path / "test_results.csv"

    result = export_leads_to_csv(
        batch,
        str(output_file)
    )

    assert result == output_file
    assert output_file.exists()

    with output_file.open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == [
        "lead_id",
        "service_interest",
        "urgency",
        "reason",
        "needs_review"
    ]

    assert len(rows) == 2


# Test 2: Correct lead data is exported
def test_csv_data_accuracy(tmp_path):

    batch = create_sample_batch()

    output_file = tmp_path / "accuracy.csv"

    export_leads_to_csv(
        batch,
        str(output_file)
    )

    with output_file.open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        rows = list(csv.DictReader(file))

    assert rows[0]["lead_id"] == "L001"
    assert rows[0]["urgency"] == "high"
    assert rows[0]["needs_review"] == "False"

    assert rows[1]["lead_id"] == "L002"
    assert rows[1]["urgency"] == "medium"
    assert rows[1]["needs_review"] == "True"


# Test 3: Unicode text is preserved
def test_csv_unicode_support(tmp_path):

    batch = create_sample_batch()

    output_file = tmp_path / "unicode.csv"

    export_leads_to_csv(
        batch,
        str(output_file)
    )

    with output_file.open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        rows = list(csv.DictReader(file))

    assert rows[0]["reason"] == "গ্রাহকের জরুরি প্রয়োজন।"


@pytest.mark.parametrize(
    "field_name",
    [
        "lead_id",
        "reason"
    ]
)
@pytest.mark.parametrize(
    "unsafe_value",
    [
        "=1+1",
        "+1+1",
        "-1+1",
        "@SUM(A1:A2)",
        "＝1+1",
        "＋1+1",
        "－1+1",
        "＠SUM(A1:A2)",
        "\t=1+1",
        "\r=1+1",
        "\n=1+1",
        " =1+1",
        " \t=1+1",
        "\u00a0=1+1"
    ]
)
def test_csv_formula_injection_is_neutralized(
    tmp_path,
    unsafe_value,
    field_name
):

    lead_data = {
        "lead_id": "L001",
        "service_interest": "other",
        "urgency": "low",
        "reason": "Normal customer message.",
        "needs_review": True
    }

    # Inject unsafe value into the selected field
    lead_data[field_name] = unsafe_value

    batch = LeadQualificationBatch(
        results=[lead_data]
    )

    output_file = tmp_path / "security_test.csv"

    export_leads_to_csv(
        batch,
        str(output_file)
    )

    with output_file.open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        rows = list(csv.DictReader(file))

    assert rows[0][field_name] == "'" + unsafe_value
