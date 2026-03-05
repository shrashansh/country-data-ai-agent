from typing import Dict, List, Optional


def normalize_country_data(raw: Dict) -> Dict:
    """
    Convert a raw REST Countries API response into a simplified structure.
    """

    name: Optional[str] = raw.get("name", {}).get("common")

    capital_list: List = raw.get("capital") or []
    capital: Optional[str] = capital_list[0] if capital_list else None

    population: Optional[int] = raw.get("population")
    region: Optional[str] = raw.get("region")
    area: Optional[float] = raw.get("area")

    languages_raw = raw.get("languages") or {}
    languages: List[str] = (
        list(languages_raw.values()) if isinstance(languages_raw, dict) else []
    )

    currencies_raw = raw.get("currencies") or {}
    currencies: List[str] = [
        meta.get("name")
        for meta in currencies_raw.values()
        if meta.get("name")
    ] if isinstance(currencies_raw, dict) else []

    timezones: List[str] = raw.get("timezones") or []

    return {
        "name": name,
        "capital": capital,
        "population": population,
        "region": region,
        "area": area,
        "languages": languages,
        "currencies": currencies,
        "timezones": timezones,
    }