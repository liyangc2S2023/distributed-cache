from flask import Flask, request, jsonify
import threading
import time
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class SlowDB:
    """
    A database that takes a long time to respond to requests.
    The delay is design to distinguish between cache hits and cache misses.
    the default delay of a request is 3 seconds.
    """
    def __init__(self, port):
        """
        Initialize the database.
        :param port: the port number of the database.
        """
        self.app = Flask(__name__)
        self.database = {}
        self.lock = threading.Lock()
        self.port = port
        self.delay = 3

        self.app.add_url_rule('/get', view_func=self.get_value, methods=['GET'])
        self.app.add_url_rule('/put', view_func=self.put_value, methods=['PUT'])
        self.app.add_url_rule('/clear', view_func=self.clear_database, methods=['DELETE'])
        self.app.add_url_rule('/delay/<secs>', view_func=self.change_delay, methods=['PUT'])

    def change_delay(self, secs):
        """
        Change the delay of the database.
        """
        self.delay = int(secs)
        return jsonify({'result': 'success'}), 200

    def get_value(self):
        """
        Get the value of a key from the database.
        """
        time.sleep(self.delay)
        key = request.args.get('key')

        with self.lock:
            value = self.database.get(key)

        if value is None:
            return jsonify({'error': 'Key not found'}), 404
        else:
            return jsonify({'key': key, 'value': value}), 200

    def put_value(self):
        """
        Put a key-value pair into the database.
        """
        data = request.get_json()

        if 'key' not in data or 'value' not in data:
            return jsonify({'error': 'Invalid request'}), 400

        key, value = data['key'], data['value']

        with self.lock:
            self.database[key] = value

        return jsonify({'result': 'success'}), 200
    
    def clear_database(self):
        """
        Clear the database.
        """
        with self.lock:
            self.database.clear()

        return jsonify({'result': 'success'}), 200

    def run(self):
        """
        Run the database.
        """
        self.app.run(host='127.0.0.1', port=self.port, debug=False)


if __name__ == '__main__':
    slowdb_port = 8000
    slowdb_server = SlowDB(slowdb_port)
    slowdb_server.run()