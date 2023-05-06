import requests
from helper import print_error_message, clear_data
import time
import random

def test_get_non_existing_key():
    """
    Test the GET request to the cache cluster when the key does not exist.
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        # send a GET request to the cache cluster
        response = requests.get('http://localhost:10000/cache/one')
        assert response.status_code == 404, 'cache cluster should have the key'

        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0

def test_get_existing_key():
    """
    Test the GET request to the cache cluster when the key exists.
    The fist GET request will miss the key in the cache cluster and get the key from the slowdb.
    The second GET request will hit the key in the cache cluster.
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        # put a key-value pair into the slowdb
        data = {'key': 'one', 'value': '1'}
        response = requests.put('http://localhost:8000/put', json=data)
        assert response.status_code == 200 and response.json()['result'] == 'success'

        # check caches miss the key and get the key from slowdb
        port = random.choice(cache_ports)
        start_time = time.time()
        response = requests.get(f'http://localhost:{port}/cache/one')
        end_time = time.time()
        time_taken = end_time - start_time
        assert response.status_code == 200 \
            and time_taken >= 3.0 \
            and response.json() == {'key': 'one', 'receiver_cache_port': port, 'value': '1'}, \
        f'cache {port} should have the key and will take over 3 secs to get the key, but took {time_taken} secs and the response is {response.json()}'
        # send a GET request to the cache cluster
        start_time = time.time()
        response = requests.get('http://localhost:10000/cache/one')
        end_time = time.time()
        time_taken = end_time - start_time
        assert response.status_code == 200 \
            and time_taken <= 1.5 \
            and response.json()['key'] == 'one' \
            and response.json()['value'] == '1', \
        f'cache cluster should have the key and will take less than 1.5 secs to get the key, but took {time_taken} secs and the response is {response.json()}'

        clear_data(cache_ports)
        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0
