"""Provider boundary for nearby dermatologist discovery.

No listings are fabricated: a real Places provider must be configured before
the API returns results.
"""
from dataclasses import dataclass
import os


class LocationProviderNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class NearbySearch:
    latitude: float | None = None
    longitude: float | None = None
    query: str | None = None


def search_dermatologists(search: NearbySearch) -> dict[str, object]:
    if not os.getenv("GOOGLE_PLACES_API_KEY"):
        raise LocationProviderNotConfigured(
            "Nearby listings require GOOGLE_PLACES_API_KEY. Configure an approved Places provider before enabling live results."
        )
    # Deliberately fail closed until a provider adapter is configured. This
    # prevents presenting invented names, ratings, addresses, or phone numbers.
    raise LocationProviderNotConfigured("The configured Places provider adapter is not enabled.")
