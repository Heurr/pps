#!/bin/bash

set -e

function alter_template() {
    echo "Alter template"
    psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" <<-EOSQL
	    \c template1
	    CREATE EXTENSION IF NOT EXISTS "ltree" SCHEMA public;
EOSQL
}

function create_user() {
    local user=$1
    local password=$2

    echo "Creating user '${user}'"
    psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" <<-EOSQL
        CREATE USER "${user}" WITH PASSWORD '${password}';
EOSQL
}

function create_database() {
	local database=$1
	local user=$2
	echo "Creating database '${database}' with owner '${user}'"
	psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" <<-EOSQL
	    CREATE DATABASE "${database}" WITH OWNER "${user}";

	    GRANT ALL PRIVILEGES ON DATABASE "${database}" TO "${user}";
EOSQL
}

if [[ -n "${PPS_DB_USER}" && -n "${PPS_DB_NAMES}" ]]; then
	alter_template
	create_user "${PPS_DB_USER}" "${PPS_DB_PASSWORD}"

	for db in $(echo "${PPS_DB_NAMES}" | tr ',' ' '); do
		create_database "${db}" "${PPS_DB_USER}"
	done

	echo "DB user and databases are created"
fi
