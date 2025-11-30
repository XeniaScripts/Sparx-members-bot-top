#!/bin/bash
# Install PostgreSQL client libraries needed to compile psycopg2
apt-get update
apt-get install -y libpq-dev
