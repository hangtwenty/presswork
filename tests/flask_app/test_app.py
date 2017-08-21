""" minimal Flask app (for now) calls for a minimal test suite (for now)
"""
import pytest


@pytest.mark.usefixtures("testapp")
class TestSmokeTests(object):

    def test_index(self, testapp):
        """ Tests if the index page loads """

        response = testapp.get('/')
        assert response.status_code == 200

# TODO definitely intend to do more than smoketests for this