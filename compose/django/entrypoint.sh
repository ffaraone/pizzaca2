#!/bin/bash
set -e
cmd="$@"

# This entrypoint is used to play nicely with the current cookiecutter configuration.
# Since docker-compose relies heavily on environment variables itself for configuration, we'd have to define multiple
# environment variables just to support cookiecutter out of the box. That makes no sense, so this little entrypoint
# does all this for us.
export REDIS_URL=redis://pizza-redis:6379

# the official postgres image uses 'postgres' as default user if not set explictly.
if [ -z "$POSTGRES_USER" ]; then
    export POSTGRES_USER=postgres
fi


export SEARCH_URL=elasticsearch://pizza-elastic:9200/pizzaca/

export DATABASE_URL=postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@pizza-postgres:5432/$POSTGRES_USER


function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(dbname="$POSTGRES_USER", user="$POSTGRES_USER", password="$POSTGRES_PASSWORD", host="pizza-postgres")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

function elastic_ready(){
python << END
import sys
import elasticsearch
try:
	conn = elasticsearch.Elasticsearch('http://pizza-elastic:9200/')
	conn.ping()
except:
    sys.exit(-1)
sys.exit(0)
END
}


until elastic_ready; do
  >&2 echo "Elasticsearch is unavailable - sleeping"
  sleep 1
done
>&2 echo "Elasticsearch is up - continuing..."


until postgres_ready; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing..."
exec $cmd
