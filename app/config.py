import os

from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")

# REST Countries API
REST_COUNTRIES_BASE_URL: str = os.getenv(
    "REST_COUNTRIES_BASE_URL",
    "https://restcountries.com/v3.1",
)

REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))

# Fields the agent is allowed to return
SUPPORTED_COUNTRY_FIELDS: list[str] = [
    "capital",
    "population",
    "currencies",
    "region",
    "languages",
    "area",
    "timezones",
]