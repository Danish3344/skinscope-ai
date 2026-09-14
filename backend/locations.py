"""Provider boundary for nearby dermatologist discovery.

No listings are fabricated: a real Places provider must be configured before
the API returns results.
"""
from dataclasses import dataclass
import os
import httpx


class LocationProviderNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class NearbySearch:
    latitude: float | None = None
    longitude: float | None = None
    query: str | None = None


def search_dermatologists(search: NearbySearch) -> dict[str, object]:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not api_key:
        raise LocationProviderNotConfigured(
            "Nearby listings require GOOGLE_PLACES_API_KEY. Configure an approved Places provider before enabling live results."
        )
    if search.latitude is not None:
        text_query = f"dermatologist near {search.latitude},{search.longitude}"
        location_bias = {"circle": {"center": {"latitude": search.latitude, "longitude": search.longitude}, "radius": 10000}}
    else:
        text_query = f"dermatologist in {search.query}"
        location_bias = None
    body = {"textQuery": text_query, "languageCode": "en"}
    if location_bias:
        body["locationBias"] = location_bias
    fields = "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.nationalPhoneNumber,places.googleMapsUri"
    try:
        response = httpx.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": fields},
            json=body,
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise LocationProviderNotConfigured("The Google Places service is temporarily unavailable.") from exc
    if response.status_code in (401, 403):
        raise LocationProviderNotConfigured("The Google Places API key is invalid or lacks Places API permission.")
    if response.status_code == 429:
        raise LocationProviderNotConfigured("Google Places quota has been exceeded. Try again later.")
    if response.status_code >= 400:
        raise LocationProviderNotConfigured("Google Places returned an API error. Check project billing and API configuration.")
    places = response.json().get("places", [])
    results = []
    for place in places:
        display = place.get("displayName", {})
        results.append({
            "id": place.get("id"),
            "name": display.get("text", ""),
            "address": place.get("formattedAddress", ""),
            "rating": place.get("rating"),
            "rating_count": place.get("userRatingCount"),
            "phone": place.get("nationalPhoneNumber"),
            "map_url": place.get("googleMapsUri"),
        })
    return {"results": results}
