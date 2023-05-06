import requests
from helper import print_error_message, clear_data
import time

def test_put_cache_aside():
    """
    check put request with cache aside pattern
    1. cache cluster will send a put request to slowdb
    2. slowdb will update the key-value pair
    3. cache cluster will not send a put request to cache servers, so cache servers will not have the key-value pair
    4. cache cluster will invalidate the cache servers with the key -> send a delete request to all cache servers
    :return: 20 if pass, 0 if fail
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        key = 'one'
        value = '1'
        # send a PUT request with key-value pair ('one', '1') to the cache cluster
        response = requests.put(f'http://localhost:10000/cache/{key}', json={'value': value})
        assert response.status_code == 200, \
            'cache cluster should put the key-value pair to slowdb'

        # check the slowdb has the key-value pair
        response = requests.get(f'http://localhost:8000/get?key={key}')
        assert response.status_code == 200 and response.json()['value'] == value, \
            f'slowdb should have the value {value} for key {key}'

        # cache servers should not have the key-value pair
        for port in cache_ports:
            response = requests.get(f'http://localhost:{port}/cache/status')
            assert response.status_code == 200 and response.json()['cache_size'] == 0, \
                f'cache server {port} should not have a key-value pair'

        # send a GET request to the cache cluster, there should be a cache miss and get the key from slowdb
        # it will take 3 seconds to get the value from slowdb
        # then cache cluster will cache the key-value pair. one of the cache servers will have the key-value pair
        start_time = time.time()
        response = requests.get('http://localhost:10000/cache/one')
        time_taken = time.time() - start_time
        assert response.status_code == 200 and response.json()['value'] == '1' and time_taken > 3, \
            'cache cluster should get the key-value pair from slowdb and cache the key-value pair'
        received_port = response.json()['receiver_cache_port']
        for port in cache_ports:
            response = requests.get(f'http://localhost:{port}/cache/status')
            if port == received_port:
                assert response.status_code == 200 and response.json()['cache_size'] == 1, \
                    f'cache server {port} should have the key-value pair'

        # send a new PUT request to change the value of the key to the cache cluster
        # new value is '0'
        new_value = '0'
        response = requests.put('http://localhost:10000/cache/one', json={'value': new_value})
        assert response.status_code == 200, \
            f'cache cluster should put the new value {new_value} to slowdb and invalidate cache servers with the key'

        # check the slowdb has the new key-value pair
        response = requests.get('http://localhost:8000/get?key=one')
        assert response.status_code == 200 and response.json()['value'] == new_value, \
            f'slowdb should have the new value {new_value} for key {key}'

        # by cache aside pattern, caches with the key should be invalidated
        # the cache server with the key should delete the key-value pair
        response = requests.get(f'http://localhost:{received_port}/cache/status')
        assert response.status_code == 200 and response.json()['cache_size'] == 0, \
            f'cache server {received_port} should not have the key-value pair'

        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0

def test_put_non_existing_key():
    """
    test can put a non-existing key-value pair to the cache cluster
    :return: 10 if pass, 0 if fail
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        key = 'one'
        value = '1'
        # get a non-existing key from the cache cluster
        response = requests.get(f'http://localhost:10000/cache/{key}')
        assert response.status_code == 404, \
            'cache cluster should not have the key-value pair'

        # send a PUT request with key-value pair ('one', '1') to the cache cluster
        response = requests.put(f'http://localhost:10000/cache/{key}', json={'value': value})
        assert response.status_code == 200, \
            'cache cluster should put the key-value pair'

        # get the key-value pair from slowdb
        response = requests.get(f'http://localhost:8000/get?key={key}')
        assert response.status_code == 200 and response.json()['value'] == value, \
            'slowdb should have the key-value pair'

        #  get the key-value pair from the cache cluster
        response = requests.get(f'http://localhost:10000/cache/{key}')
        assert response.status_code == 200 and response.json()['value'] == value, \
            f'cache cluster should have the key-value pair'

        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0


def test_put_existing_key():
    """
    test can put an existing key with new val to the cache cluster
    :return: 10 if pass, 0 if fail
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        # add a key-value pair to the slowdb
        key = 'one'
        value = '1'
        data = {'key': key, 'value': value}
        response = requests.put('http://localhost:8000/put', json=data)
        assert response.status_code == 200, \
            'slowdb should add the key-value pair'

        # send a GET request to the cache cluster
        start_time = time.time()
        response = requests.get('http://localhost:10000/cache/one')
        assert response.status_code == 200 and response.json()['value'] == value, \
            'cache cluster should get the key-value pair from slowdb and cache the key-value pair'

        # send a PUT request with new key-value pair ('one', '0') to the cache cluster
        new_value = '0'
        response = requests.put(f'http://localhost:10000/cache/{key}', json={'value': new_value})
        assert response.status_code == 200, \
            'cache cluster should put the new key-value pair'

        # get the new key-value pair from slowdb
        response = requests.get(f'http://localhost:8000/get?key={key}')
        assert response.status_code == 200 and response.json()['value'] == new_value, \
            'slowdb should have the new key-value pair'

        #  get the new key-value pair from the cache cluster
        response = requests.get(f'http://localhost:10000/cache/{key}')
        assert response.status_code == 200 and response.json()['value'] == new_value, \
            'cache cluster should get the new key-value pair'

        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0
