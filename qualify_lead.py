import os

from dotenv import load_dotenv
from openai import OpenAI

from lead_schemas import LeadQualification


# Load environment variables
load_dotenv(override=True)

# Create OpenAI client
client = OpenAI()


def qualify_lead(lead_message: str):

    response = client.responses.parse(
        model="gpt-6-luna",

        input=[
            {
                "role": "system",
                "content": """
                You are an AI lead qualification assistant.

                Analyze the customer's message.

                Identify:
                1. The service they are interested in.
                2. How urgent their requirement is.
                3. Why you selected this classification.
                4. Whether human review is required.

                Use only the information provided.
                Never invent missing information.

                If the message is unclear or insufficient,
                set needs_review to true.
                """
            },
            {
                "role": "user",
                "content": lead_message
            }
        ],

        text_format=LeadQualification,
        max_output_tokens=200,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "No structured output returned by the AI."
        )

    return result


if __name__ == "__main__":

    sample_lead = """
    I run a marketing agency and need an AI
    automation system to manage my leads.

    This is urgent because we are receiving
    too many customer inquiries.
    """

    print("Analyzing lead...\n")

    qualification = qualify_lead(sample_lead)

    print("AI LEAD QUALIFICATION RESULT")
    print("============================")

    print(qualification.model_dump_json(indent=2))