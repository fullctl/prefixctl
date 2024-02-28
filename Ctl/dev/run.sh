#!/bin/bash

COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_NAME=$(basename $(git rev-parse --show-toplevel))$(basename $COMPOSE_DIR)

# check for UID / github actions
if [[ -n "$UID" ]]; then
  run_options="-u $UID"
fi

docker-compose -p $PROJECT_NAME -f $COMPOSE_DIR/docker-compose.yml run $run_options django $@
