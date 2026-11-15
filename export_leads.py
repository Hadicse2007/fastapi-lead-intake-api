
import csv
from pathlib import Path

from lead_schemas import LeadQualificationBatch


def safe_csv_value(value):

    if not isinstance(value, str):
        return value

    # Identify leading whitespace characters
    stripped_value = value.lstrip()

    leading_whitespace = value[
        :len(value) - len(stripped_value)
    ]

    # Spreadsheet formula prefixes
    dangerous_prefixes = (
        "=",
        "+",
        "-",
        "@",
        "＝",
        "＋",
        "－",
        "＠"
    )

    # Check for dangerous control characters
    has_dangerous_control = any(
        char in ("\t", "\r", "\n")
        for char in leading_whitespace
    )

    # Neutralize potentially dangerous spreadsheet values
    if (
        has_dangerous_control
        or stripped_value.startswith(dangerous_prefixes)
    ):
        return "'" + value

    return value



def export_leads_to_csv(
    batch: LeadQualificationBatch,
    output_file: str = "lead_qualification_results.csv"
):

    output_path = Path(output_file)

    fieldnames = [
        "lead_id",
        "service_interest",
        "urgency",
        "reason",
        "needs_review"
    ]

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for lead in batch.results:

            row = lead.model_dump()

            safe_row = {
                key: safe_csv_value(value)
                for key, value in row.items()
            }

            writer.writerow(safe_row)

    return output_path
