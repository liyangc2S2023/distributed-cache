import requests

from tests.helper import clear_data, print_error_message


def test_replication():
    """
    test the replication of the cache cluster
    a key-value pair should be replicated to all cache servers if there are more than 10 get requests for the key
    :return: 25 if pass, 0 if fail
    """
    try:
        cache_ports = [8001, 8002, 8010]
        # clear the cache cluster
        clear_data(cache_ports)

        # put a key-value pair into the slowdb
        data = {'key': 'one', 'value': '1'}
        response = requests.put('http://localhost:8000/put', json=data)
        assert response.status_code == 200, \
            'slowdb should have the key-value pair'

        # # send a GET request to the cache cluster
        # response = requests.get('http://localhost:10000/cache/one')
        # # get the receiver cache server
        # receiver_port = response.json()['receiver_cache_port']

        # # check the receiver cache server has one key-value pair and other cache servers don't have no key-value pair
        # for port in cache_ports:
        #     response = requests.get(f'http://localhost:{port}/cache/status')
        #     assert response.status_code == 200
        #     if port == receiver_port:
        #         assert response.json()['cache_size'] == 1, \
        #             f'cache {port} should have one key-value pair'
        #     else:
        #         assert response.json()['cache_size'] == 0, \
        #             f'cache {port} should not have any key-value pair'

        # send 10 GET requests for the same key to the cache cluster,
        # the cache cluster will replicate the key-value pair to all cache servers
        # the default replication threshold is 10
        for _ in range(10):
            response = requests.get('http://localhost:10000/cache/one')
            assert response.status_code == 200, \
                'cache cluster should handle 10 GET requests for the same key'

        # check all cache servers have the key-value pair
        for port in cache_ports:
            response = requests.get(f'http://localhost:{port}/cache/status')
            assert response.status_code == 200 \
                and response.json()['cache_size'] == 1, \
                f'cache {port} should have one key-value pair'

        return 25
    except AssertionError as e:
        print_error_message(str(e))
        return 0