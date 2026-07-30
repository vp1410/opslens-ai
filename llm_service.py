from openai import OpenAI

from config import OPENAI_MODEL, validate_config


def create_openai_client() -> OpenAI:
    """Validate configuration and create the OpenAI client."""

    validate_config()

    return OpenAI()


def test_llm_connection() -> str:
    """Send a small request to verify that the LLM connection works."""

    client = create_openai_client()

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a concise technical assistant. "
            "Answer in one sentence."
        ),
        input=(
            "Explain what a duplicate-key database error means."
        ),
    )

    return response.output_text


def main() -> None:
    """Run a basic LLM connectivity test."""

    print("Testing OpenAI connection...")

    answer = test_llm_connection()

    print("\nModel response:")
    print(answer)


if __name__ == "__main__":
    main()