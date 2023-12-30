CREATE DATABASE IF NOT EXISTS a2s;

CREATE TABLE IF NOT EXISTS a2s.servers (
	timestamp DateTime DEFAULT NOW(),
	ip String,
	port UInt16
)
ENGINE = MergeTree
ORDER BY (timestamp, ip, port)
TTL timestamp + INTERVAL 6 HOUR
SETTINGS merge_with_ttl_timeout = 3600;

CREATE TABLE IF NOT EXISTS a2s.info (
    timestamp DateTime CODEC(Delta(4), ZSTD(1)),
    address LowCardinality(String),
    server_name LowCardinality(String),
    map_name LowCardinality(String),
    game LowCardinality(String),
    player_count UInt8,
    max_players UInt8,
    bot_count UInt8,
    server_type LowCardinality(String),
    platform LowCardinality(String),
    password_protected UInt8,
    vac_enabled UInt8,
    version LowCardinality(String),
    ping Float32
)
ENGINE = MergeTree
ORDER BY (address, timestamp)
TTL timestamp + toIntervalDay(7);

CREATE TABLE IF NOT EXISTS a2s.players (
    timestamp DateTime CODEC(Delta(4), ZSTD(1)),
    address LowCardinality(String),
    name String,
    score Int32,
    duration Float32
)
ENGINE = MergeTree
ORDER BY (address, timestamp)
TTL timestamp + toIntervalDay(7);