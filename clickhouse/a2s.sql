CREATE DATABASE IF NOT EXISTS a2s;

CREATE TABLE IF NOT EXISTS a2s.info (
timestamp default now(),
address LowCardinality(String),
server_name LowCardinality(String),
map_name LowCardinality(String),
game LowCardinality(String),
player_count UInt32,
max_players UInt32,
bot_count UInt32,
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

CREATE TABLE IF NOT EXISTS  a2s.players (
timestamp DateTime default now(),
address LowCardinality(String),
name String,
 score UInt32,
 duration Float32
)
ENGINE = MergeTree
ORDER BY (address, timestamp)
TTL timestamp + toIntervalDay(7);
