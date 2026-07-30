import os

from dotenv import load_dotenv


# Load values from the local .env file into environment variables.
load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Keep the model name in one place so it is easy to change later.
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5-mini",
)


def validate_config() -> None:
    """Validate required application configuration."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is missing. "
            "Add it to the project's .env file."
        )