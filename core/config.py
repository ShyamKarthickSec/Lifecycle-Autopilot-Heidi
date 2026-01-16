from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    # Model choices — tuned for cost/quality balance
    model_fast: str = "gpt-4o-mini"
    model_quality: str = "gpt-4o-mini"  # can upgrade to "gpt-4o" if you want
    slack_webhook_url: str | None = None

    @staticmethod
    def load() -> "AppConfig":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Create a .env file from .env.example and add your key."
            )
        slack = os.getenv("SLACK_WEBHOOK_URL", "").strip() or None
        return AppConfig(openai_api_key=key, slack_webhook_url=slack)
