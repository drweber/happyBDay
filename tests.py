from app import app, database, models

passed=0
not_passed=0

with app.app.test_client() as c:
    rv_on_put_success = c.put('/hello/test', json=
    {
        'dateOfBirth': '1925-12-10'
    }
                             )
    rv_on_put_failed = c.put('/hello/test', json=
    {
        'dateOfBirth': '1500-22-10'
    }
                             )
    rv_on_post_failed = c.post('/hello/test', json=
    {
        'dateOfBirth': '1995-12-10'
    }
                             )
    rv_on_get_success = c.get('/hello/test')
    rv_on_get_failed = c.get('/hello/super_uniq_name')
    rv_on_get_location_failed = c.get('/super_uniq_name')
    assert rv_on_put_success.status_code == 204 or 201, "PUT success NOT passed"
    print("PUT success passed")
    assert rv_on_put_failed.status_code == 400, "PUT failed NOT passed"
    print("PUT failed passed")
    assert rv_on_post_failed.status_code == 405, "POST failed NOT passed"
    print("POST failed passed")
    assert rv_on_get_success.status_code == 200, "GET success NOT passed"
    print("GET success passed")
    assert rv_on_get_failed.status_code == 404, "GET failed NOT passed"
    print("GET failed passed")
    assert rv_on_get_location_failed.status_code == 404, "GET location failed NOT passed"
    print("GET location failed passed")
    print("+++++++++++++++++++++")
    print("All test are passed")