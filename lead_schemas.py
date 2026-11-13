from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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