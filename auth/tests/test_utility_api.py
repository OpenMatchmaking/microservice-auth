from conftest import sanic_server  # NOQA


async def test_health_check_returns_ok(sanic_server):
    url = sanic_server.app.url_for('health-check')
    response = await sanic_server.get(url)
    response_body = await response.text()
    assert response.status == 200
    assert response_body == 'OK.'


async def test_health_check_post_not_allowed(sanic_server):
    url = sanic_server.app.url_for('health-check')
    response = await sanic_server.delete(url)
    assert response.status == 405


async def test_health_check_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for('health-check')
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_health_check_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for('health-check')
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_health_check_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for('health-check')
    response = await sanic_server.delete(url)
    assert response.status == 405
