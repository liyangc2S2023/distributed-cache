import os
import signal
import time

import subprocess
import sys

def kill_process_on_port(port):
    """
    Kill the process using the specified port.
    """
    command = f"lsof -i :{port} -t"
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        pids = result.strip().split('\n')
        for pid in pids:
            if pid:
                os.kill(int(pid), signal.SIGTERM)
    except subprocess.CalledProcessError:
        # No process found using the specified port
        pass

def main():
    """
    Start the SlowDB server, the cache cluster and the cache servers.
    """
    for port in [10000, 8001, 8002, 8010, 8000]:
        kill_process_on_port(port)
    cache_ports = [8001, 8002, 8010]

    # Start the SlowDB server
    slowdb_process = subprocess.Popen(['python3', 'slowdb.py'])

    cluster_process = subprocess.Popen(['python3', 'cache_proxy.py', '10000'])
    time.sleep(2)
    # Start the cache servers
    cache_processes = [
        subprocess.Popen(['python3', 'cache_server.py', str(port), '10000']) for port in cache_ports
    ]

    # Wait for all subprocesses to complete
    slowdb_process.wait()
    cluster_process.wait()
    for process in cache_processes:
        process.wait()


if __name__ == '__main__':
    main()