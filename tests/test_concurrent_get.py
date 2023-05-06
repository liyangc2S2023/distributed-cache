from helper import put_and_get_random_keys, print_error_message, clear_data
import time
import concurrent
import requests
import math

def test_concurrency_get():
    """
    test can get keys concurrently from the cache cluster
    :return: 20 if pass, 0 if fail
    """
    num_keys = 60
    num_threads = 10
    cache_cluster_url = 'http://127.0.0.1:10000'
    avg_response_time_threshold = 0.5
    clear_data([8001, 8002, 8010])

    def get_key(cache_cluster_url, key, expected_value):
        start_time = time.time()
        response = requests.get(f"{cache_cluster_url}/cache/{key}")
        end_time = time.time()
        
        assert response.status_code == 200 and response.json()['value'] == expected_value, f"Failed to GET key: {key}"
        
        response_time = end_time - start_time
        return response_time
    

    try:
        # warm up the cache
        keys = put_and_get_random_keys(cache_cluster_url, num_keys)

        # get keys concurrently
        response_times = []
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_key, cache_cluster_url, key, value) for key, value in keys.items()]
            for future in concurrent.futures.as_completed(futures):
                response_times.append(future.result())
        end_time = time.time()

        get_time = end_time - start_time
        # Calculate average response time
        average_response_time = math.fsum(response_times) / len(response_times)

        assert average_response_time <= avg_response_time_threshold, f"Average response time: {average_response_time} is greater than threshold: {avg_response_time_threshold}"
        return 25
    except AssertionError as e:
        print_error_message(str(e))
        return 0