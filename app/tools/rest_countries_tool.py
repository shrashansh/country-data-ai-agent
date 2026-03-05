import logging

import requests

from app.config import REQUEST_TIMEOUT, REST_COUNTRIES_BASE_URL

logger = logging.getLogger(__name__)


def fetch_country_data(country: str) -> dict:
    """Fetch country data from the REST Countries API by name.

    Args:
        country: The country name to look up.

    Returns:
        The first matching country object from the API response.

    Raises:
        ValueError: If the country is not found or the API returns an error.
        requests.RequestException: If a network-level error occurs.
    """
    country = country.strip()
    url = f"{REST_COUNTRIES_BASE_URL}/name/{country}"
    logger.info("Fetching country data for %r from %s", country, url)

    response = requests.get(url, timeout=REQUEST_TIMEOUT)

    if response.status_code == 404:
        logger.warning("Country not found: %r (HTTP 404)", country)
        raise ValueError(f"Country not found: '{country}'")

    if not response.ok:
        logger.error(
            "Unexpected response for country %r: HTTP %d", country, response.status_code
        )
        raise ValueError(
            f"Failed to fetch data for '{country}': HTTP {response.status_code}"
        )

    data = response.json()

    if not data:
        logger.warning("Empty response body for country: %r", country)
        raise ValueError(f"Country not found: '{country}'")

    if len(data) > 1:
        logger.info("Multiple matches found for %r, selecting first result", country)

    logger.info("Successfully fetched data for %r", country)

    return data[0]