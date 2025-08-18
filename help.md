### Проверка формата для ClickHouse:
curl -X POST "http://0.0.0.0:8123/?query=INSERT%20INTO%20logs%20FORMAT%20JSONEachRow" -H "Content-Type: application/json" --user admin:admin --data-binary '{"event_id":1,"level":"MAIN - info","service":"main.py:simulate_user_session:30","stream_id":"bffc3672-bd39-4055-bba9-c6a217feaf77","timestamp":"2025-02-21 10:02:03","user_id":41401}'


### Зайти в ClickHouse Client:
docker exec -it clickhouse clickhouse-client --host localhost --port 9000 --user admin --password admin


### Общий размер данных на диске и количество строк:
SELECT
    database,
    formatReadableSize(sum(bytes_on_disk)) AS total_size,
    sum(rows) AS total_rows
FROM system.parts
GROUP BY database
ORDER BY total_size DESC;


### Очистка логов system.query_log:
TRUNCATE TABLE system.query_log;


SELECT
    database,
    sum(bytes_on_disk) / 1024 / 1024 AS db_size_mb
FROM system.parts
WHERE database = 'default'
GROUP BY database