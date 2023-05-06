from helper import clear_data, print_error_message
import requests
import random
import time

def test_cache_communication():
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)
        data = {'value': '1'}
        response = requests.put('http://localhost:8001/cache/one', json=data)

        response2 = requests.get(f'http://localhost:8010/cache/one')
        assert response2.status_code == 200 and response2.json()['value'] == '1', \
            f'cache should get the key-value pair by communicating with other cache servers'
        
        start_time = time.time()
        response = requests.get(f'http://localhost:8010/cache/one')
        end_time = time.time()
        time_diff = end_time - start_time
        assert response.status_code == 200 and time_diff <= 1.0, f'selected port should not cache miss'
        clear_data(cache_ports)
        
        return 10
    except AssertionError as e:
        print_error_message(str(e))
        return 0