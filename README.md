# DomainTracker

A simple widget to track the life of domains based on keyword.

#### Dependencies:
* requests
* psycopg2
* a postgres database with schema and functions defined in ddl.sql


#### Example execution:

python3 GetDomainData.py 'lava' rds_connection_string
