# from unittest.mock import patch, Mock

import pytest
import pandas as pd

from main import app
from utils.lastfm import get_data

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client
