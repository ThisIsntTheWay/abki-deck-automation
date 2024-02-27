#!/bin/sh
set -e

HOST=$([ "$1" ] && echo "$1" || echo "localhost:8765")
ANKI_FOLDER=$([ "$2" ] && echo "$2" || echo "anki")
EXPORT_PATH=$([ "$3" ] && echo "$3" || echo "anki.apkg")

if ! [[ $EXPORT_PATH =~ ".apkg" ]]; then
    echo "[X] EXPORT_PATH ($EXPORT_PATH) is not an .apkg file."
    exit 1
else
    # Append /opt to ANKI_FOLDER if in container
    if [ -f /.dockerenv ]; then
        # Remove ./ or / from beginning of string
        trimmed_string="${ANKI_FOLDER#./}" && trimmed_string="${trimmed_string#/}"
        ANKI_FOLDER="/opt/$trimmed_string"
    fi
fi

echo "Rendering '$ANKI_FOLDER' to '$EXPORT_PATH' with AnkiConnect at '$HOST'."

python check.py "$ANKI_FOLDER"
python assemble.py "$ANKI_FOLDER" "$EXPORT_PATH" "$HOST"
