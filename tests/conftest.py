import pytest
import gensim.downloader as api

@pytest.fixture
def model():
    yield api.load("20-newsgroups")