from collections import OrderedDict


class LRUCache:
    """
    This is an LRU cache implementation with a fixed capacity.
    """

    def __init__(self, max_len):
        """
        :param max_len: the maximum data length of the cache.
        """
        self.max_len = max_len
        self.cache = OrderedDict()

    def add(self, key, value):
        """
        Add a key-value pair to the cache. If the key already exists, it will overwrite the least recently used value.
        :param key:
        :param value:
        :return:
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            self.cache[key] = value

        while len(self.cache) > self.max_len:
            self.remove_lru()

    def get(self, key):
        """
        Get the value of a key. If the key does not exist, return None.
        :param key: the key to get
        :return: the value of the key, and a boolean indicating whether the key exists
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key], True
        return None, False

    def remove_lru(self):
        """
        Remove the least recently used item from the cache.
        :return: None
        """
        if len(self.cache) == 0:
            return
        # remove the least recently used item
        self.cache.popitem(last=False)

    def len(self):
        """
        Get the number of items in the cache.
        :return: the number of items in the cache
        """
        return len(self.cache)
    
    def clear(self):
        """
        Clear the cache.
        :return: None
        """
        self.cache.clear()

    def delete(self, key):
        """
        Delete a key from the cache.
        :param key: the key to delete
        :return: None
        """
        if key in self.cache:
            del self.cache[key]
