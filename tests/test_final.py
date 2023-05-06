import time
from test_slowdb import test_slowdb
from test_init import test_cache_ports_registered
from test_get_key import test_get_non_existing_key, test_get_existing_key
from test_put_key import (
    test_put_non_existing_key,
    test_put_existing_key,
    test_put_cache_aside,
)
from test_lru_cache import test_lru_cache
from test_consistent_hashing import test_consistent_hashing
from test_ch_distribution import test_consistent_hashing_distribution
from test_replication import test_replication
from test_fault_tolerance import test_fault_tolerance
from test_concurrent_get import test_concurrency_get
from test_cache_communication import test_cache_communication
import threading
import os
import subprocess
import signal
import argparse


def kill_process_on_port(port):
    """
    Kill the process using the specified port
    :param port: port number
    :return: None
    """
    command = f"lsof -i :{port} -t"
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        pids = result.strip().split("\n")
        for pid in pids:
            if pid:
                os.kill(int(pid), signal.SIGTERM)
    except subprocess.CalledProcessError:
        # No process found using the specified port
        pass

def main(kill_ports, stop_event=None):
    """
    Start the SlowDB server, the cache cluster and the cache servers
    :param stop_event: stop event
    :return: None
    """
    if kill_ports:
        print("Killing processes on ports")
        for port in [10000, 8001, 8002, 8010, 8000]:
            kill_process_on_port(port)

    cache_ports = [8001, 8002, 8010]

    # Start the SlowDB server
    slowdb_process = subprocess.Popen(["python3", "slowdb.py"])

    cluster_process = subprocess.Popen(["python3", "cache_proxy.py", "10000"])
    time.sleep(2)
    # Start the cache servers
    cache_processes = [
        subprocess.Popen(["python3", "cache_server.py", str(port), "10000"])
        for port in cache_ports
    ]

    if stop_event:
        stop_event.wait()
        slowdb_process.terminate()
        cluster_process.terminate()
        for process in cache_processes:
            process.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run tests with optional kill_ports flag')
    parser.add_argument('--kill_ports', type=bool, default=False,
                        help='Set to True to kill processes on ports, default is False')

    args = parser.parse_args()
    score = 0
    main_thread = threading.Thread(target=main, args=(args.kill_ports,))
    main_thread.start()
    time.sleep(5)
    print("------------------start of test----------------------")
    tests = [
        test_lru_cache,
        test_consistent_hashing,
        test_slowdb,
        test_cache_ports_registered,
        test_get_non_existing_key,
        test_get_existing_key,
        test_put_non_existing_key,
        test_put_existing_key,
        test_cache_communication,
        test_put_cache_aside,
        test_consistent_hashing_distribution,
        test_replication,
        test_fault_tolerance,
        test_concurrency_get
    ]
    for test in tests:
        result = test()
        if result != 0:
            score += result
            print(f"{test.__name__}: PASS +{result}")
        else:
            print(f"{test.__name__}: FAIL")
    print("------------------end of test----------------------")
    print(f"Total Score: {score} / 200")
    main_thread.join()
