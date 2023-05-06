import hashlib
import bisect

class ConsistentHashing:
    """
    An implementation of consistent hashing.
    """
    def __init__(self, num_replicas=10):
        """
        Initialize a consistent hashing object.
        :param num_replicas: number of virtual nodes for each cache server. default is 10.
        """
        self.num_replicas = num_replicas
        self.hash_ring = []
        self.nodes = {}

    def _hash(self, key):
        """
        Hash the key using sha256.
        """
        key = str(key).encode('utf-8')
        return int(hashlib.sha256(key).hexdigest(), 16)

    def _generate_virtual_nodes(self, node):
        """
        Generate virtual nodes for a given node.
        """
        return [f'{node}_{i}' for i in range(self.num_replicas)]

    def add_node(self, node):
        """
        Add a node to the hash ring.
        """
        virtual_nodes = self._generate_virtual_nodes(node)
        for virtual_node in virtual_nodes:
            hashed_key = self._hash(virtual_node)
            bisect.insort(self.hash_ring, hashed_key)
            self.nodes[hashed_key] = node

    def remove_node(self, node):
        """
        Remove a node from the hash ring.
        """
        virtual_nodes = self._generate_virtual_nodes(node)
        for virtual_node in virtual_nodes:
            hashed_key = self._hash(virtual_node)
            self.hash_ring.remove(hashed_key)
            del self.nodes[hashed_key]

    def get_node(self, key):
        """
        Get the node for a given key.
        """
        hashed_key = self._hash(key)
        index = bisect.bisect(self.hash_ring, hashed_key)
        if index == len(self.hash_ring):
            index = 0
        return self.nodes[self.hash_ring[index]]
