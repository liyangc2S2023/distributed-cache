import requests
import concurrent
import uuid

def print_error_message(message):
    """
    Helper to print the error message in yellow color
    :param message: error message
    :return: None
    """
    print('\033[93m' + message + '\033[0m')


def clear_data(cache_ports):
    """
    Helper to clear the data in slowdb and cache servers
    :param cache_ports: list of cache ports
    :return: None
    """
    for port in cache_ports:
        response = requests.delete(f'http://localhost:{port}/cache/clear')
        assert response.status_code == 200, f'cache {port} should be cleared'
    response = requests.delete('http://localhost:8000/clear')
    assert response.status_code == 200, 'slowdb should be cleared'

def put_and_get_random_keys(cache_cluster_url, num_keys):
    """
    Helper to put and get random keys to the cache cluster
    :param cache_cluster_url: url of the cache cluster
    :param num_keys: number of keys to put and get
    :return: a dictionary of keys and values
    """
    keys = {}
    
    def put_and_get_key(cache_cluster_url, key, value):
        response = requests.put(f"{cache_cluster_url}/cache/{key}", json={'value': value})
        assert response.status_code == 200, f"Failed to PUT key: {key}"
        
        get_res = requests.get(f"{cache_cluster_url}/cache/{key}")
        assert get_res.status_code == 200 and get_res.json()['value'] == value, f"Failed to GET key: {key}"

    requests.put('http://127.0.0.1:8000/delay/0')
    
    # Send PUT requests with different keys
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(num_keys):
            key = str(uuid.uuid4())
            keys[key] = f"value{i}"
            future = executor.submit(put_and_get_key, cache_cluster_url, key, f"value{i}")
            futures.append(future)
        concurrent.futures.wait(futures)

    requests.put('http://127.0.0.1:8000/delay/3')

    return keys