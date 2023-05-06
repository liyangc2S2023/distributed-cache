import bisect
from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from consistent_hash import ConsistentHashing


def test_consistent_hashing():
    """
    Test the consistent hashing basic functionalities.
    :return: 10 if pass, 0 if fail
    """
    try:
        test_add_node()
        test_remove_node()
        test_get_node_returns_correct_node()
        test_get_node_after_node_removal()
        return 10
    except:
        return 0


def test_add_node():
    """
    Test adding a node to the hash ring.
    """
    ch = ConsistentHashing()
    ch.add_node("node1")
    assert "node1" in ch.nodes.values()


def test_remove_node():
    """
    Test removing a node from the hash ring.
    """
    ch = ConsistentHashing()
    ch.add_node("node1")
    ch.remove_node("node1")
    assert "node1" not in ch.nodes.values()


def test_get_node_returns_correct_node():
    """
    Test that get_node returns the correct node for a given key.
    """
    ch = ConsistentHashing()
    nodes = ['node1', 'node2', 'node3']
    for node in nodes:
        ch.add_node(node)

    keys = ['key1', 'key2', 'key3']
    expected_node_map = _generate_expected_node_map(ch, keys)

    for key in keys:
        node = ch.get_node(key)
        assert node == expected_node_map[key]


def test_get_node_after_node_removal():
    """
    Test that get_node returns the correct node for a given key after a node is removed.
    """
    ch = ConsistentHashing()
    nodes = ['node1', 'node2', 'node3']
    for node in nodes:
        ch.add_node(node)
    # remove node2
    ch.remove_node('node2')
    keys = ['key1', 'key2', 'key3']
    expected_node_map = _generate_expected_node_map(ch, keys)

    for key in keys:
        node = ch.get_node(key)
        assert node == expected_node_map[key]


def _generate_expected_node_map(ch, keys):
    """
    helper function to generate the expected node map for a given list of keys
    """
    hash_ring = ch.hash_ring
    node_map = ch.nodes

    expected_node_map = {}

    for key in keys:
        hashed_key = ch._hash(key)
        index = bisect.bisect(hash_ring, hashed_key)
        if index == len(hash_ring):
            index = 0
        node = node_map[hash_ring[index]]
        expected_node_map[key] = node

    return expected_node_map