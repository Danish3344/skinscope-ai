from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_location_requires_explicit_query_or_coordinates() -> None:
    response = client.get('/dermatologists')
    assert response.status_code == 400


def test_location_fails_closed_without_provider_credentials(monkeypatch) -> None:
    monkeypatch.delenv('GOOGLE_PLACES_API_KEY', raising=False)
    response = client.get('/dermatologists', params={'query': 'Pune'})
    assert response.status_code == 503
    assert 'GOOGLE_PLACES_API_KEY' in response.json()['detail']
