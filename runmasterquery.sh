#!/bin/bash
cd "$(dirname "$0")"
docker compose run --rm a2s-masterquery
