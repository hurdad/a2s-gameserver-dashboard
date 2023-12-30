#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime
from a2s import ainfo, aplayers
from clickhouse_driver import Client
import time
import logging
import signal

m_shutdown = 0  # global shutdown variable
logger = logging.getLogger(__name__)


# signal shutdown when receive SIGHUP/SIGINT
def receive_signal(signalNumber, frame):
    logger.info('Signal Received : {}'.format(signalNumber))
    global m_shutdown
    m_shutdown = 1
    return


async def get_server_info(address, timeout):
    try:
        info = await ainfo(address=(address[0], address[1]), timeout=timeout)
    except Exception as e:
        logger.error(f"An error occurred while querying {address}: {e}")
        return address, None
    return address, info


async def get_player_info(address, timeout):
    try:
        info = await aplayers(address=(address[0], address[1]), timeout=timeout)
    except Exception as e:
        logger.error(f"An error occurred while querying {address}: {e}")
        return address, None
    return address, info


async def process(conf):
    # Connect to ClickHouse server
    client = Client(host=conf["CLICKHOUSE_HOST"], port=int(conf["CLICKHOUSE_PORT"]), database='a2s')

    # query for servers
    query = '''
        SELECT ip, port
        FROM a2s.servers s
        GROUP BY ip, port
    '''

    # Execute the query
    servers_to_query = client.execute(query)

    # Get current timestamp to use for the timestamp ClickHouse Column
    current_timestamp = datetime.now()

    # Create tasks to query server info for each address
    tasks = [get_server_info(address, conf["TIMEOUT"]) for address in servers_to_query]

    # Gather and run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Process the collected results
    info_data_batch = []
    for r in results:
        address = r[0]
        info = r[1]
        if info:
            info_data = {
                "timestamp": current_timestamp,
                "address": ":".join(map(str, address)),
                "server_name": info.server_name,
                "map_name": info.map_name,
                "game": info.game,
                "player_count": info.player_count,
                "max_players": info.max_players,
                "bot_count": info.bot_count,
                "server_type": info.server_type,
                "platform": info.platform,
                "password_protected": 1 if info.password_protected else 0,
                "vac_enabled": 1 if info.vac_enabled else 0,
                "version": info.version,
                "ping": info.ping
            }
            info_data_batch.append(info_data)

    # batch insert into clickhouse
    client.execute(
        query='INSERT INTO a2s.info (timestamp, address, server_name, map_name, game, player_count, max_players, bot_count, server_type, platform, password_protected, vac_enabled, version, ping) VALUES',
        params=info_data_batch
    )
    logger.debug('info inserted {}'.format(len(info_data_batch)))

    # Create tasks to query server info for each address
    tasks = [get_player_info(address, conf["TIMEOUT"]) for address in servers_to_query]

    # Gather and run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Process the collected results
    player_data_batch = []
    for r in results:
        address = r[0]
        players = r[1]
        if players:
            for p in players:
                player_data = {
                    "timestamp": current_timestamp,
                    "address": ":".join(map(str, address)),
                    "name": p.name.replace("'", "''"),
                    "score": p.score,
                    "duration": p.duration}
                player_data_batch.append(player_data)

    # batch insert into clickhouse
    client.execute(
        query='INSERT INTO a2s.players (timestamp, address, name, score, duration) VALUES',
        params=player_data_batch
    )
    logger.debug('players inserted {}'.format(len(player_data_batch)))


def config_from_env():
    config = {}

    config["CLICKHOUSE_HOST"] = os.environ.get("CLICKHOUSE_HOST") if os.environ.get(
        "CLICKHOUSE_HOST") is not None else "localhost"

    config["CLICKHOUSE_PORT"] = int(os.environ.get("CLICKHOUSE_PORT")) if os.environ.get(
        "CLICKHOUSE_PORT") is not None else 9000

    config["INTERVAL"] = int(os.environ.get("INTERVAL")) if os.environ.get(
        "INTERVAL") is not None else 10

    config["TIMEOUT"] = int(os.environ.get("TIMEOUT")) if os.environ.get(
        "TIMEOUT") is not None else 1

    return config


if __name__ == "__main__":
    # get config from ENV
    conf = config_from_env()

    # configure logging
    logging.basicConfig(format="%(asctime)s [%(name)s:%(lineno)d][%(funcName)s][%(levelname)s] %(message)s")

    # register SIGHUP and SIGINT signals to be caught
    signal.signal(signal.SIGHUP, receive_signal)
    signal.signal(signal.SIGINT, receive_signal)

    # Run the main coroutine
    while not m_shutdown:
        # start time
        start_time = time.time()
        try:
            asyncio.run(process(conf))
        except Exception as e:
            logger.error(f"An error occurred : {e}")

        # calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time

        # sleep for INTERVAL - execution time
        time.sleep(conf["INTERVAL"] - execution_time)

    print('Exiting..')
