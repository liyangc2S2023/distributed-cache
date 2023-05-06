import unittest
from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from lru_cache import LRUCache


def test_lru_cache():
    """
    Test the LRU cache basic functionalities.
    :return: 10 if pass, 0 if fail
    """
    try:
        test_add_new_key()
        test_get_key()
        test_update_key()
        test_len()
        test_remove_lru()
        return 10
    except:
        return 0


def test_add_new_key():
    """
    Test adding a new key-value pair to the cache.
    :return: None
    """
    lru_cache = LRUCache(1)
    lru_cache.add("one", 1)
    value, found = lru_cache.get("one")
    assert found == True


def test_get_key():
    """
    Test getting a key from the cache.
    :return: None
    """
    lru_cache = LRUCache(1)
    value, found = lru_cache.get("one")
    assert found == False
    lru_cache.add("one", 1)
    value, found = lru_cache.get("one")
    assert found == True


def test_update_key():
    """
    Test update an existing key.
    :return: None
    """
    lru_cache = LRUCache(1)
    lru_cache.add("one", 1)
    lru_cache.add("one", "1")
    value, found = lru_cache.get("one")
    assert found == True


def test_len():
    """
    Test getting the number of items in the cache.
    :return: None
    """
    lru_cache = LRUCache(3)
    lru_cache.add("one", 1)
    assert lru_cache.len() == 1
    lru_cache.add("two", 2)
    assert lru_cache.len() == 2
    # update an existing key does not change the length
    lru_cache.add("two", 3)
    assert lru_cache.len() == 2


def test_remove_lru():
    """
    Test removing the least recently used item.
    :return: None
    """
    lru_cache = LRUCache(3)
    lru_cache.add("one", 1)
    lru_cache.add("two", 2)
    lru_cache.add("three", 3)

    # Test that the cache is full
    assert lru_cache.len() == lru_cache.max_len

    # Test that the LRU item is removed
    lru_cache.add("four", 4)
    value, found = lru_cache.get("one")
    assert found == False

def test_delete():
    """
    Test deleting a key from the cache.
    :return: None
    """
    lru_cache = LRUCache(2)
    lru_cache.add("one", 1)
    lru_cache.add("two", 2)
    lru_cache.delete("one")
    value, found = lru_cache.get("one")
    assert found == False
    assert lru_cache.len() == 1
