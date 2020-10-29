import sys
import datetime
import logging
import requests
import psycopg2

logging.basicConfig(filename='domaintracker.log', encoding='utf-8', level=logging.INFO)


def search_domainsdb(keyword):
    """Perform a keyword search against the domainsdb.info API and return list of domains"""
    domains = {}
    url = "https://api.domainsdb.info/v1/domains/search?page=2&limit=50&domain={keyword}".format(keyword=keyword)
    response = requests.get(url)
    
    for item in response.json()['domains']:
        domain = item['domain']
        domains[domain] = 'None'

    return domains


def get_active_domains_from_db(sql_cursor):
    """Call a postgres function to list all active domains in db.
    
    A domain is 'Active' when the newest max(timestamp) record for the domain
    has Action = 'Added'.

    sql_cursor -- Cursor from an open psycopg2 connection
    """

    sql_cursor.execute("SELECT * FROM get_active_domain_records()")
    db_domains = sql_cursor.fetchall()
    active_domains = {}
    for domain in db_domains:
        active_domains[domain[1]] = domain[2]

    return active_domains


def get_inactive_domains_from_db(sql_cursor):
    """Call a postgres function to list all inactive domains in db.
    
    A domain is 'Inactive' when the newest max(timestamp) record for the domain
    has Action = 'Removed'.

    sql_cursor -- Cursor from an open psycopg2 connection
    """

    sql_cursor.execute("SELECT * FROM get_active_domain_records()")
    db_domains = sql_cursor.fetchall()
    inactive_domains = {}
    for domain in db_domains:
        inactive_domains[domain[1]] = domain[2]

    return inactive_domains


def get_list_of_additions(api_domains, active_domains):
    """Return a list of domains to add to the database"""

    dont_add_list = []
    add_list = []
    for domain in api_domains:
        if domain not in active_domains:
            add_list.append(domain)

    return add_list


def get_list_of_deletions(api_domains, active_domains):
    """Return a list of domains to delete from the database"""

    delete_list = []
    for domain in active_domains:
        if domain not in api_domains:
            delete_list.append(domain)

    return delete_list


def insert_domain_records(domains_to_insert, action, sql_connection):
    """Insert domain records into the database.
    
    domains_to_insert -- list of domains to be inserted
    action -- Domain status. Can be 'Added' or 'Removed'
    sql_connection -- an open psycopg2 connection
    """

    domains = '{' + ', '.join(domains_to_insert) + '}'
    actions = '{' + ((action + ', ') * len(domains_to_insert))[:-2] + '}'
    timestamp = str(datetime.datetime.now())
    timestamps = '{' + ((timestamp + ', ') * len(domains_to_insert))[:-2] + '}'

    cursor = sql_connection.cursor()
    cursor.execute("CALL insert_domain_records(%s, %s, %s);", (domains, actions, timestamps))
    sql_connection.commit()

    logging.info("{} -- {} {} domains".format(timestamp, action, len(domains_to_insert)))


def main(search_keyword, connection_string):
    try:
        sql_connection = psycopg2.connect(connection_string)
    except:
        logging.exception("{} -- Could not connect to database. Exiting".format(str(datetime.datetime.now())))
        sys.exit("Could not connect to database. Exiting")

    sql_cursor = sql_connection.cursor()
    
    api_domains = search_domainsdb(search_keyword)
    active_domains = get_active_domains_from_db(sql_cursor)

    add_list = get_list_of_additions(api_domains, active_domains)
    delete_list = get_list_of_deletions(api_domains, active_domains)

    insert_domain_records(add_list, "Added", sql_connection)
    insert_domain_records(delete_list, "Removed", sql_connection)



if __name__ == "__main__":
    search_keyword = sys.argv[1]
    rds_connection_string = sys.argv[2]
    main(search_keyword, rds_connection_string)






