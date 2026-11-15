from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LeadQualification(BaseModel):

    model_config = ConfigDict(extra="forbid")

    service_interest: Literal[
        "marketing_automation",
        "crm_integration",
        "lead_generation",
        "other"
    ] = Field(
        description="The service the lead is interested in."
    )

    urgency: Literal[
        "low",
        "medium",
        "high"
    ] = Field(
        description="How urgent the lead's requirement is."
    )

    reason: str = Field(
        description="Explain the classification using evidence from the lead message."
    )

    needs_review: bool = Field(
        description="Whether a human should review this lead."
    )

class LeadQualificationItem(LeadQualification):

    lead_id: str = Field(
        description="The exact ID of the input lead being classified."
    )


class LeadQualificationBatch(BaseModel):

    model_config = ConfigDict(extra="forbid")

    results: list[LeadQualificationItem] = Field(
    min_length=1,
    description="At least one qualification result for each batch."
)

    @model_validator(mode="after")
    def validate_unique_lead_ids(self):

        lead_ids = [
            item.lead_id for item in self.results
        ]

        if len(lead_ids) != len(set(lead_ids)):
            raise ValueError(
                "Duplicate lead_id found in batch."
            )

        return self