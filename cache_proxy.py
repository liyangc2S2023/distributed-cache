from flask import Flask, request, jsonify
import sys
from consistent_hash import ConsistentHashing
import requests
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class CacheCluster:
    """
    Cache Cluster is responsible for handling all the requests from the client.
    it will distribute the requests to the cache servers based on the consistent hashing algorithm.
    """

    def __init__(self, consistent_hash, slowdb_host, port, replication_threshold=10):
        """
        Initialize a cache cluster.
        :param consistent_hash: a consistent hashing object.
        :param slowdb_host: the host of slowdb.
        :param port: the port of the cache cluster.
        :param replication_threshold: the threshold of replication. default is 10.
        """
        self.app = Flask(__name__)
        self.consistent_hash = consistent_hash
        self.slowdb_host = slowdb_host
        self.port = port
        self.cache_servers = set()
        self.key_access_count = {}
        self.replication_threshold = replication_threshold
        self.app.add_url_rule('/cache/<key>', view_func=self.cache_operations, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule('/status', view_func=self.get_status, methods=['GET'])
        self.app.add_url_rule('/register', view_func=self.register_cache_server, methods=['POST'])

    def get_status(self):
        """
        This endpoint is used to get the status of the cache cluster
        :return: status code 200 and a list of registered cache server.
        """
        server_status = {}
        for server in self.cache_servers:
            response = requests.get(f'http://{server}/cache/status')
            if response.status_code != 200:
                return jsonify({'error': f'Error getting status from {server}'}), 500
            server_status[server] = response.json()['cache_size']
        return jsonify({'status': 'OK', 'cache_servers': list(self.cache_servers), 'server_status': server_status}), 200

    def cache_operations(self, key):
        """
        define GET and PUT requests to the cache cluster.
        """
        if request.method == 'GET':
            return self._get_value(key)
        elif request.method == 'PUT':
            value = request.get_json(force=True)['value']
            return self._put_value(key, value)
        
    def register_cache_server(self):
        """
        Register a cache server to the cache cluster.
        """
        server = request.get_json()['server']
        if server not in self.cache_servers:
            self.cache_servers.add(server)
            self.consistent_hash.add_node(server)
            return jsonify({'result': 'success'}), 200
        else:
            return jsonify({'result': 'Server already registered'}), 400

    def _get_cache_server(self, key):
        """
        Get the cache server that stores the key.
        """
        cache_server = self.consistent_hash.get_node(key)
        return f'http://{cache_server}'

    def _get_value(self, key):
        """
        a helper to handle GET request to get a value by key from a cache server.
        :return: 200 if successfully get a value from cache server; 404 if the key if not found by the cache server.
        """
        cache_server_url = self._get_cache_server(key)
        response = requests.get(f'{cache_server_url}/cache/{key}')
        if response.status_code == 404:
            return jsonify(response.json()), 404
        else:
            # Increment access count
            self.key_access_count[key] = self.key_access_count.get(key, 0) + 1
            if self.key_access_count[key] >= self.replication_threshold:
                self._replicate_key(key, response.json()["value"])
            return jsonify(response.json()), 200

    def _put_value(self, key, value):
        """
        a helper to handle PUT request to put value by key.

        cache aside pattern:
        1. Update value in slowdb
        2. Invalidate the old value in cache with the key (delete the key-value pair in cache)

        :return: 200 if successfully put the key-value pair to the slowdb and invalidated all cache servers with the key;
        otherwise, return 500.
        """
        # Update value in slowdb
        response = requests.put(f'http://{self.slowdb_host}/put', json={'key': key, 'value': value})
        if response.status_code != 200:
            return jsonify({'error': 'Failed to update slowdb'}), 500
        # Invalidate the value in cache with the key
        # send a delete request to all cache servers, if a cache server has the key, it will delete it
        for cache_server in self.cache_servers:
            cache_server_url = f'http://{cache_server}'
            response = requests.delete(f'{cache_server_url}/cache/{key}')
            # if response.status_code != 200:
            #     logging.error(f"Failed to invalidate key '{key}' in cache server '{cache_server}'")
        return jsonify({'result': 'success'}), 200

    def _replicate_key(self, key, value):
        """
        replicate a key-value pair to all cache servers if there are 10 GET requests for the same key.
        """
        for cache_server in self.cache_servers:
            cache_server_url = f'http://{cache_server}'
            response = requests.put(f'{cache_server_url}/cache/{key}', json={'value': value})
            if response.status_code != 200:
                logging.error(f"Failed to replicate key '{key}' to cache server '{cache_server}'")

    def run(self):
        self.app.run(host='127.0.0.1', port=self.port, debug=False)

if __name__ == '__main__':
    slowdb_host = '127.0.0.1'
    slowdb_port = 8000
    cache_proxy_port = int(sys.argv[1])
    cache_proxy = CacheCluster(ConsistentHashing(), f'{slowdb_host}:{slowdb_port}', cache_proxy_port)
    cache_proxy.run()
