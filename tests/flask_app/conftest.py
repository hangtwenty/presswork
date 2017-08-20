import pytest


@pytest.fixture()
def testapp(request):
    from presswork.flask_app.app import app
    client = app.test_client()

    # # # TODO(hangtwenty) setup/teardown of dbs for textmakers - ensure they are using pytest tmpdir fixture...
    # # def teardown():
    # #     pass
    #
    # request.addfinalizer(teardown)

    return client