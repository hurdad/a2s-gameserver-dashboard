#!/usr/bin/env python3
import os
import logging
import valve.source
import valve.source.master_server
from clickhouse_driver import Client


def config_from_env():
    config = {}

    config["CLICKHOUSE_HOST"] = os.environ.get("CLICKHOUSE_HOST") if os.environ.get(
        "CLICKHOUSE_HOST") is not None else "localhost"

    config["CLICKHOUSE_PORT"] = int(os.environ.get("CLICKHOUSE_PORT")) if os.environ.get(
        "CLICKHOUSE_PORT") is not None else 9000

    return config


if __name__ == "__main__":
    # get config from ENV
    conf = config_from_env()

    # configure logging
    logging.basicConfig(format="%(asctime)s [%(name)s:%(lineno)d][%(funcName)s][%(levelname)s] %(message)s")

    # Connect to ClickHouse server
    client = Client(host=conf["CLICKHOUSE_HOST"], port=int(conf["CLICKHOUSE_PORT"]), database='a2s')

    # query master server
    msq = valve.source.master_server.MasterServerQuerier()
    res = msq.find(region=[u"na"], gamedir=u"tf", empty=u"1")

    # convert to dict
    addresses = []
    for address in res:
        addresses.append({"ip": address[0], "port": address[1]})

    # batch insert into clickhouse
    client.execute(
        query='INSERT INTO a2s.servers (ip, port) VALUES',
        params=addresses
    )
    print("inserted ips : {}".format(len(addresses)))
