import requests

def test_cache_ports_registered():
    """
    Test if all cache servers are registered by cache cluster
    :return: 10 if pass, 0 if fail
    """
    try:
        cache_ports = [8001, 8002, 8010]

        # Check if all cache servers are registered
        response = requests.get('http://127.0.0.1:10000/status')
        registered_servers = response.json()['cache_servers']

        for port in cache_ports:
            server = f'127.0.0.1:{port}'
            assert server in registered_servers
        return 10
    except:
        return 0

