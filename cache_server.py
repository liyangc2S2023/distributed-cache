from flask import Flask, request, jsonify
import sys
import requests
import threading
from lru_cache import LRUCache
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class CacheServer:
    """
    Cache servers are responsible to handle client request passed by cache clusters.

    Each cache server hosts a lru cache to store key-value pairs.
    If a key is not found in the cache, the cache server will try to pass the request to the next cache server in the cluster.
    If the key is not found in the cluster, the cache server will try to get the value from the slowdb.
    Then the responding cache server will store the key-value pair in the cache.
    """

    def __init__(self, lru_cache_size, slowdb_host, port) -> None:
        """
        Initialize a cache server.
        :param lru_cache_size: the size of the lru cache
        :param slowdb_host: the host of the slowdb
        :param port: the port of the cache server
        """
        self.app = Flask(__name__)
        self.cache = LRUCache(lru_cache_size)
        self.cache_lock = threading.Lock()
        self.slowdb_host = slowdb_host
        self.port = port
        self.registered = False
        self.is_stop = False

        # Register the cache_operations method as a route
        self.app.add_url_rule('/cache/<key>', view_func=self.cache_operations, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule('/cache/clear', view_func=self.clear_cache, methods=['DELETE'])
        self.app.add_url_rule('/cache/status', view_func=self.status, methods=['GET'])
        self.app.add_url_rule('/cache/control', view_func=self.control, methods=['PUT'])
    
    def status(self):
        """
        Get the status of the cache server.
        """
        return jsonify({'cache_size': self.cache.len(), 'receiver_cache_port': self.port}), 200
    
    def control(self):
        """
        Control the cache server to run or stop.
        """
        state = request.get_json(force=True)['state']
        self.is_stop = state == 'stop'
        return jsonify({'result': 'success', 'receiver_cache_port': self.port, 'is_stop': self.is_stop}), 200

    def cache_operations(self, key):
        """
        handle GET, POST, DELETE requests to the cache server.
        """
        if self.is_stop:
            return jsonify({'error': 'Cache is stopped', 'receiver_cache_port': self.port}), 500
        if request.method == 'GET':
            check_others = request.args.get('check_others', default='true', type=str).lower() == 'true'
            value = self._get_value(key, check_others)
            if value is None:
                return jsonify({'error': 'Key not found', 'receiver_cache_port': self.port}), 404
            else:
                return jsonify({'key': key, 'value': value, 'receiver_cache_port': self.port}), 200
        elif request.method == 'PUT':
            value = request.get_json(force=True)['value']
            return self._put_value(key, value)
        elif request.method == 'DELETE':
            return self._delete_key(key)
        
    def clear_cache(self):
        """
        Clear the lru cache hosted by the cache server.
        """
        with self.cache_lock:
            self.cache.clear()
        return jsonify({'result': 'success', 'receiver_cache_port': self.port}), 200

    def _get_value_from_slowdb(self, key):
        """
        Get the value by key from the slowdb.
        : param key: the key of the key-value pair
        : return: the value of the key-value pair
        """
        response = requests.get(f'http://{self.slowdb_host}/get?key={key}')
        
        if response.status_code == 404:
            return None
        else:
            return response.json()['value']

    def _get_value(self, key, check_others=True):
        """
        Get the value by key from the cache.
        If the key is not found in the cache, get the value from the slowdb.
        : param key: the key of the key-value pair
        : return: the value of the key-value pair
        """
        with self.cache_lock:
            value, found = self.cache.get(key)

        if not found and check_others:
            other_cache_servers = self._get_other_cache_servers()
            for cache_server in other_cache_servers:
                response = requests.get(f'http://{cache_server}/cache/{key}?check_others=false')
                if response.status_code != 404:
                    value = response.json()['value']
                    break

        if not found and not value:
            value = self._get_value_from_slowdb(key)

        if value:
            with self.cache_lock:
                self.cache.add(key, value)
        else:
            return None

        return value
    
    def _get_other_cache_servers(self):
        """
        Get the addresses of next cache servers in the cluster.
        """
        response = requests.get(f'http://{self.cluster_address}/status')
        if response.status_code == 200:
            cache_servers = response.json()['cache_servers']
            cache_servers.remove(f'127.0.0.1:{self.port}')
            return cache_servers
        else:
            return []

    def _put_value(self, key, value):
        """
        Put the key-value pair into the cache.
        """
        with self.cache_lock:
            self.cache.add(key, value)

        if not self._put_value_in_slowdb(key, value):
            return jsonify({'error': 'Failed to update slowdb'}), 500

        return jsonify({'result': 'success', 'receiver_cache_port': self.port}), 200

    def _put_value_in_slowdb(self, key, value):
        """
        Put the key-value pair into the slowdb.
        """
        response = requests.put(f'http://{self.slowdb_host}/put', json={'key': key, 'value': value})
        if response.status_code == 200:
            return jsonify({'result': 'success', 'receiver_cache_port': self.port}), 200
        else:
            return jsonify({'error': 'Failed to update slowdb', 'receiver_cache_port': self.port}), 500

    def _delete_key(self, key):
        """
        Delete the key-value pair by key from the cache.
        """
        with self.cache_lock:
            self.cache.delete(key)
        return jsonify({'result': 'success', 'receiver_cache_port': self.port}), 200

    def run(self):
        """
        Run the cache server.
        """
        self.app.run(host='127.0.0.1', port=self.port, debug=False)

    def register_with_cluster(self, cluster_address):
        """
        Register the cache server with the cache cluster.
        """
        if not self.registered:
            self.cluster_address = cluster_address
            response = requests.post(f'http://{cluster_address}/register', json={'server': f'127.0.0.1:{self.port}'})
            if response.status_code == 200:
                print(f"Cache server registered with the cache cluster at {cluster_address}")
                self.registered = True
            else:
                print(f"Failed to register with the cache cluster at {cluster_address}: {response.json()['result']}")


if __name__ == '__main__':
    lru_cache_size = 100
    slowdb_host = '127.0.0.1'
    slowdb_port = 8000
    cache_port = int(sys.argv[1])
    cluster_port = int(sys.argv[2])
    cluster_addr = f'127.0.0.1:{cluster_port}'
    print("Starting cache server on port", cache_port, "and registering with cluster at", cluster_addr)

    cache_server = CacheServer(lru_cache_size, f'{slowdb_host}:{slowdb_port}', cache_port)
    cache_server.register_with_cluster(cluster_addr)
    cache_server.run()