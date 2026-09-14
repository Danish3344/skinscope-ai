from fastapi.testclient import TestClient

from backend.main import app
from backend import locations

client = TestClient(app)


def test_location_requires_explicit_query_or_coordinates() -> None:
    response = client.get('/dermatologists')
    assert response.status_code == 400


def test_location_fails_closed_without_provider_credentials(monkeypatch) -> None:
    monkeypatch.delenv('GOOGLE_PLACES_API_KEY', raising=False)
    response = client.get('/dermatologists', params={'query': 'Pune'})
    assert response.status_code == 503
    assert 'GOOGLE_PLACES_API_KEY' in response.json()['detail']


def test_location_maps_provider_response_without_inventing_fields(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200
        def json(self):
            return {'places': [{'id': 'p1', 'displayName': {'text': 'Clinic'}, 'formattedAddress': 'Address', 'googleMapsUri': 'https://maps.google.com/?q=clinic'}]}
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY', 'test-key')
    monkeypatch.setattr(locations.httpx, 'post', lambda *args, **kwargs: FakeResponse())
    response = client.get('/dermatologists', params={'query': 'Pune'})
    assert response.status_code == 200
    assert response.json()['results'][0] == {'id': 'p1', 'name': 'Clinic', 'address': 'Address', 'rating': None, 'rating_count': None, 'phone': None, 'map_url': 'https://maps.google.com/?q=clinic'}


def test_location_rejects_invalid_provider_key(monkeypatch) -> None:
    class FakeResponse:
        status_code = 403
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY', 'invalid')
    monkeypatch.setattr(locations.httpx, 'post', lambda *args, **kwargs: FakeResponse())
    response = client.get('/dermatologists', params={'query': 'Pune'})
    assert response.status_code == 503
    assert 'invalid' in response.json()['detail']


def test_location_handles_quota_and_empty_results(monkeypatch) -> None:
    class EmptyResponse:
        status_code = 200
        def json(self): return {'places': []}
    monkeypatch.setenv('GOOGLE_PLACES_API_KEY', 'test-key')
    monkeypatch.setattr(locations.httpx, 'post', lambda *args, **kwargs: EmptyResponse())
    response = client.get('/dermatologists', params={'query': 'Nowhere'})
    assert response.status_code == 200
    assert response.json()['results'] == []

    class QuotaResponse:
        status_code = 429
    monkeypatch.setattr(locations.httpx, 'post', lambda *args, **kwargs: QuotaResponse())
    response = client.get('/dermatologists', params={'query': 'Pune'})
    assert response.status_code == 503
    assert 'quota' in response.json()['detail'].lower()
