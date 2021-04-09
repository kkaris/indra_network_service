from os import environ
from fastapi.testclient import TestClient

environ['API_DEBUG'] = "1"

from indra_network_search.rest_api import app

client = TestClient(app)


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'available'}
