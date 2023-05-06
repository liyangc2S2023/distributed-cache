import random
import requests
from helper import put_and_get_random_keys, clear_data, print_error_message

def test_fault_tolerance(cache_ports = [8001, 8002, 8010]):
    """
    test the fault tolerance of the cache cluster.
    client should be able to get the same key-value pair from the cache cluster even if one of the cache servers is down
    :return: 20 if pass, 0 if fail
    """
    try:
        clear_data(cache_ports)
        server_to_shutdown = cache_ports[random.randrange(0, 3)]

        keys = put_and_get_random_keys('http://127.0.0.1:10000', 50)
        # shutdown one of the cache servers
        requests.put(f'http://127.0.0.1:{server_to_shutdown}/cache/control', json={'state': 'stop'})
        # check if the cache server is shutdown
        response = requests.get(f'http://localhost:{server_to_shutdown}/cache/{next(iter(keys))}')

        assert response.status_code == 500, f'cache server {server_to_shutdown} should be shutdown'

        for key in keys:
            response = requests.get(f'http://localhost:10000/cache/{key}')
            assert response.status_code == 200, f'cache cluster should handle 50 GET requests for the same key'

        requests.put(f'http://localhost:{server_to_shutdown}/cache/control', json={'state': 'start'})

        clear_data(cache_ports)
        return 25
    except AssertionError as e:
        print_error_message(str(e))
        return 0