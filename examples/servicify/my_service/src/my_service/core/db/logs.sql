CREATE TABLE IF NOT EXISTS event
(
    id       UUID,
    ts       DateTime(9, 'UTC'),
    kind     Enum8('internal'=0, 'external'=1),
    type     LowCardinality(String),
    code     Int32  default 0,
    http_url String default '',
    rel_id   UUID   default toUUID('00000000-0000-0000-0000-000000000000')
)
    Engine = MergeTree()
        PRIMARY KEY (kind, type, ts)
        PARTITION BY (toYear(ts))
;