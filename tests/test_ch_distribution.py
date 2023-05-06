import requests
from helper import print_error_message, clear_data, put_and_get_random_keys
import concurrent.futures
import uuid

def test_consistent_hashing_distribution():
    """
    Test the consistent hashing distribution
    keys should be equally distributed among virtual nodes for the cache servers
    :return: 25 if passed, 0 if failed
    """
    cache_cluster_url = 'http://127.0.0.1:10000'
    num_keys = 300

    try:
        put_and_get_random_keys(cache_cluster_url, num_keys)

        # Get the key distribution
        response = requests.get(f"{cache_cluster_url}/status")
        assert response.status_code == 200, "Failed to get cluster status"
        key_distribution = response.json()['server_status']
        # Calculate the average number of keys per server
        total_keys = sum(key_distribution.values())
        num_servers = len(key_distribution)
        average_keys_per_server = total_keys / num_servers

        # Check if keys are equally distributed
        threshold = 0.2  # Allow a 20% deviation from the average
        for server, num_keys in key_distribution.items():
            deviation = abs(num_keys - average_keys_per_server) / average_keys_per_server
            round_deviation = round(deviation, 2)
            assert round_deviation <= threshold, f"Unequal key distribution on server {server}, deviation: {round_deviation}"

        clear_data([8001, 8002, 8010])
        return 25
    except AssertionError as e:
        print_error_message(str(e))
        return 0