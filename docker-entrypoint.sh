#!/bin/sh
set -eu

# Persisted SQLite lives here; Docker/Coolify volumes are often mounted as root:root while
# the app runs as user `app` — without this, SQLite fails with "unable to open database file".
mkdir -p /app/data
chown -R app:app /app/data || true

if [ -x /usr/sbin/runuser ]; then
  exec /usr/sbin/runuser -u app -- "$@"
fi
if [ -x /usr/bin/runuser ]; then
  exec /usr/bin/runuser -u app -- "$@"
fi
echo >&2 "ERROR: runuser not found; install util-linux in the image."
exit 1
