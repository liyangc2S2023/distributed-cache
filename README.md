## Lab 4: Implementing Distributed Cache System
Tianyu Zeng (tianyuze), Liyang Chen	 (liyangc2)

### Project Goal
For lab 4, we want to implement a distributed cache system using Python. The distributed cache system will improve query performance and reduce latency. Our distributed cache system supports load balancing, fault tolerance and concurrency.

The main idea of the distributed cache system is: If a client wants to look up a key, the cache cluster should first check whether the cluster has cached this value. Only if no matched key-value pairs are found in caches, the cluster will turn to fetch the value from a data storage (such as database, DFS etc.) and save this value to the cache cluster. Since caches store data in memory, returning data by cache will improve query performance instead of returning data from disk or a remote storage.

### Design Description
Our distributed cache system design includes three main components: 
1. Proxy server: 
A proxy server handles client requests and allocates every request to a cache server.
2. Cache server: 
A Cache server handles requests passed by the proxy server. Each cache server maintains a cache in memory. For a GET request, if the cache does not have the key, the cache server will pass a request to another cache server, or, the cache server will retrieve data from the data storage and save the data to its cache.
3. Data storage:
A data storage stores data persistently .

![dcs design.png](dcs%20design.png)

#### LRU Cache
The cache maintained by each cache server follows LRU policy. Least Recently Used (LRU), is a cache replacement policy that removes the least recently used items first when the cache reaches its capacity. This approach aims to retain more frequently accessed items in the cache, on the assumption that these items are more likely to be requested again in the future.

#### Consistent Hashing
The proxy server uses consistent hashing technique to distribute client requests across multiple servers. It provides a balanced distribution of cache keys, reduces the impact of node failures and adding/removing nodes.

The request key and the virtual nodes for cache servers are mapped to a circular keyspace called hash ring. Each node is assigned to a position on the hash ring based on its hash. Consistent hashing will return the nearest mapping node to the key regarding the position on the hash ring. 

#### Replication
If the cache cluster receives more than a threshold of (we say, 10) GET requests on a particular key, the cache cluster should replicate the data across all cache servers. This replication helps to distribute the load among the nodes and reduces the chances of a single node failure by a high volume of requests for that specific key. It will also reduce lookup latency for popular keys for future client requests.

#### Consistency: Handle PUT Request by Cache Aside Pattern
Clients can also send PUT requests to the cache cluster to add or modify a value to a key. However, if a value is modified in the data storage, how can we guarantee the data consistency between the value in data storage and the value in cache servers? 

We design to handle PUT requests by a cache aside pattern:
1. The proxy server will send a put request to the data storage to add/ update a value by a key.
2. The proxy server will invalidate the existing cached key by deleting cache data with the key.

This pattern makes sure that the cache cluster will not get dirty data from a cache. Imagine the cluster tries to handle a PUT request on the key, in the meanwhile the cluster handles a GET request on the same key. If the responding cache server results in a cache miss and retrieves and saves data from data storage before the PUT request finishes, the data saved in the cache may be inconsistent with the data in the data storage after modification by PUT request. To avoid this scenario, we want our cluster first modifying data storage first and notifying the cache next, instead of checking cache server first and modifying data storage next.

#### Fault Tolerance
We expect our distributed cache system can continue serving requests even if one or more nodes fail, ensuring high availability. 

By replication across all cache servers, the cache cluster can retrieve a frequent key with cache in a high efficiency in case of node failure.

The consistent hashing avoids reshuffling data on a hash ring when nodes are removed or added to the clusters. The request key will be allocated to the next nearest neighbor node on the hash ring. So consistent hashing also supports fault tolerance.

#### Concurrency
We expect our distributed cache system can handle concurrent requests. If there are a large amount of get requests to the cache cluster, we expect the cache cluster can handle each request in short response time on average. 


### Implementation
For this project, we implemented our distributed cache system using Python. Communication among the proxy server, cache servers and the data storage server  are connected by RESTful APIs.We use a lightweight web framework called Flask to support API calls. 

We designed a slow database server for data storage. The slowdb will simulate a database instance that will cause a 3 seconds delay when retrieving values from it. It helps to distinguish between getting value from in memory cache and getting value value from data storage in the test.

We implement LRU cache by OrderedDict in Python. This is a data structure supporting key-value storage, ordering and retrieving data from both ends of the structure.

We implement Consistent Hashing by creating hash values for request keys and virtual server nodes and implementing a hash ring by ordering the hashes.


### Tests

For testing, we came up with the following 11 test suites:
- Unit test behaviors of LRU cache. It should have the ability to store and retrieve values based on keys. It should also evict least recently used values. **(10 pts)**
- Unit test behaviors of Consistent hashing. Each server should be hased and mapped into a hash space. Moreover, each server should have its own virtual nodes. When receiving a incoming key, we should be able to find its appropriate server. **(10 pts)**
- Test initialization of servers. Each server (proxy server, cache server, and slow db server) should be started without any error and verified by hitting their endpoints. Cache servers should register their address with proxy server upon starting. **(20 pts)**
- Test cache server communication. While there is a cache miss on one server, it should make requests to other servers to check if they have the key before making query to slow db **(10 pts)**
- GET a non existing key. When client send a GET request for retrieving a non existing key, the cache server will check if slow db contains such key and return to client no such key exists after 3 seconds delay **(15 pts)**
- PUT a non existing key. When client send a PUT request to store a new key value pair. The key and value should be saved in corresponding cache server and slow db. **(10 pts)**
- GET an existing key. When client tries to get the value that's stored in previous request, it should be able to **immediately** get the correct value, no longer than 1 sec. **(10 pts)**
- PUT an existing key. When client tries to update previous key and its value, it should be able to do it right away and the result should be reflected in the slow db. **(10 pts)**
- Test cache aside policy. We will test the cache aside policy by checking if the cache server will delete the key from cache when it receives a delete request. **(10 pts)**
- Test consistent hashing. Keys should be properly distributed across the nodes. The number of key stored in each node must be within a 20% deviation from the average **(25 pts)**
- Test fault tolerance. Simulate a cache server failure by stopping one of the cache server processes, and then verify that the system can still handle requests for the keys that were originally assigned to the failed server. After the failed server is restarted, test whether it can recover its state and join the cluster again. **(25 pts)**
- Test replication. When a key is requested multiple times, we will replicate it on all servers to reduce the number of requests to the slow database. **(25 pts)**
- Test concurrent get request. When multiple clients send GET request for the same key, the cache server should only send one request to the slow db and return the same value to all clients. Average response time should be under 0.5s **(25 pts)**

### Deliverables

We include all the required packages in requirement.txt.

To build the working environment, run the following command in the command line:
`make build`

To run all tests for this project, run the following command in the command line:
`make test`
