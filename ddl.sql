create schema Domains
    create table Records (
        ID serial PRIMARY KEY,
        Domain varchar(253),
        Action varchar(7),
        TimeStamp timestamp
    )


create procedure insert_domain_records(domain text[], action text[], timestmp timestamp[])
LANGUAGE SQL
AS $$
    INSERT INTO domains.records(domain, action, timestamp)
    SELECT * FROM unnest(domain, action, timestmp)
$$;


create or replace function get_active_domain_records() returns setof domains.records AS $$
    SELECT * FROM (
        SELECT a.id, a.domain, a.action, a.timestamp
        FROM domains.records a
        JOIN (SELECT domain, max(timestamp) maxDate
                FROM domains.records
              GROUP BY domain) b
        ON a.domain = b.domain AND a.timestamp = b.maxDate) c
    WHERE action = 'Added'
$$
LANGUAGE SQL;


create or replace function get_inactive_domain_records() returns setof domains.records AS $$
    SELECT * FROM (
        SELECT a.id, a.domain, a.action, a.timestamp
        FROM domains.records a
        JOIN (SELECT domain, max(timestamp) maxDate
                FROM domains.records
              GROUP BY domain) b
        ON a.domain = b.domain AND a.timestamp = b.maxDate) c
    WHERE action = 'Removed'
$$
LANGUAGE SQL;
