#!/usr/bin/env python3

import asyncio
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


async def get_server_info(address):
    try:
        info = await ainfo(address, timeout=1)
    except Exception as e:
        print(f"An error occurred while querying {address}: {e}")
        return address, None
    return address, info


async def get_player_info(address):
    try:
        info = await aplayers(address, timeout=1)
    except Exception as e:
        print(f"An error occurred while querying {address}: {e}")
        return address, None
    return address, info


async def process():
    # Connect to ClickHouse server
    client = Client(host='localhost', port=9001, database='a2s')

    # List of server addresses to query
    servers_to_query = [
        ('45.62.160.71', 27015),
        ('91.216.250.10', 27015),
        ('91.216.250.15', 27015),
        ('91.216.250.30', 27015),
        ('91.216.250.12', 27015),
        ('91.216.250.55', 27015),
        ('91.216.250.13', 27015),
        ('91.216.250.31', 27015),
        ('91.216.250.193', 27015),
        ('91.216.250.11', 27015),
        ('91.216.250.54', 27015),
        ('91.216.250.20', 27015),
        ('91.216.250.17', 27015),
        ('91.216.250.40', 27015),
        ('91.216.250.37', 27015),
        ('91.216.250.52', 27015),
        ('91.216.250.18', 27015),
        ('91.216.250.160', 27015),
        ('91.216.250.21', 27015),
        ('91.216.250.22', 27015),
    ]

    # Create tasks to query server info for each address
    tasks = [get_server_info(address) for address in servers_to_query]

    # Gather and run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Process the collected results
    info_data_batch = []
    for r in results:
        address = r[0]
        info = r[1]
        if info:
            info_data = {
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
        query='INSERT INTO a2s.info (address, server_name, map_name, game, player_count, max_players, bot_count, server_type, platform, password_protected, vac_enabled, version, ping) VALUES',
        params=info_data_batch
    )
    logger.info('info inserted {}'.format(len(info_data_batch)))

    # Create tasks to query server info for each address
    tasks = [get_player_info(address) for address in servers_to_query]

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
                    "address": ":".join(map(str, address)),
                    "name": p.name.replace("'", "''"),
                    "score": p.score,
                    "duration": p.duration}
                player_data_batch.append(player_data)

    # batch insert into clickhouse
    client.execute(
        query='INSERT INTO a2s.players (address, name, score, duration) VALUES',
        params=player_data_batch
    )
    logger.info('players inserted {}'.format(len(player_data_batch)))


if __name__ == "__main__":
    # configure logging
    logging.basicConfig(format="%(asctime)s [%(name)s:%(lineno)d][%(funcName)s][%(levelname)s] %(message)s")

    # register SIGHUP and SIGINT signals to be caught
    signal.signal(signal.SIGHUP, receive_signal)
    signal.signal(signal.SIGINT, receive_signal)

    # Run the main coroutine
    while not m_shutdown:
        asyncio.run(process())
        time.sleep(5)

    print('Exiting..')