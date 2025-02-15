import pytest
from main import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Music Analyzer Project" in response.data
    assert b"Welcome" in response.data
