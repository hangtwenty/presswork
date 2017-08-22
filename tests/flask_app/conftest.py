import pytest


@pytest.fixture()
def testapp(request):
    from presswork.flask_app.app import app
    client = app.test_client()
    return client