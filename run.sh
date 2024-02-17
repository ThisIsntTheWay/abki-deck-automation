#!/bin/sh
set -e

HOST=$([ "$1" ] && echo "$1" || echo "localhost:8765")
ANKI_FOLDER=$([ "$2" ] && echo "$2" || echo "anki")

echo "$HOST - $ANKI_FOLDER"

python check.py "$ANKI_FOLDER"
python assemble.py "$HOST" "$ANKI_FOLDER"