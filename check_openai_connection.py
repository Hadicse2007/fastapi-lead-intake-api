import os

from dotenv import load_dotenv
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
)


def main():
    # Load environment variables
    load_dotenv(override=True)

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("ERROR: API Key not found.")

    try:
        client = OpenAI()

        print("Connecting to OpenAI...")

        response = client.responses.create(
            model="gpt-6-luna",
            input="Reply with exactly: OpenAI API connection successful.",
            max_output_tokens=30,
        )

        print("\nSUCCESS!")
        print("AI Response:", response.output_text)

    except AuthenticationError:
        print("ERROR: Invalid API Key.")

    except RateLimitError:
        print("ERROR: Rate limit or quota reached.")

    except APIConnectionError:
        print("ERROR: Connection failed.")

    except APIStatusError as error:
        print("API Error:", error.status_code)


if __name__ == "__main__":
    main()