# Anki deck automation
This repo provides tools to automatically build and export an Anki deck.  
Will require an active AnkiConnect instance.

## Usage
To assemble a deck, execute `assemble.py`:
```bash
assemble.py <host> <deck_export_path>
```
- `<host>` is the AnkiConnect instance and must be specified as `<ip>:<port>`.
- `<deck_export_path>` is the absolute path of the exported deck file.

_Additionally, the validity of the `anki` folder can be checked by running `check.py <folder>`._

As an alternative, a docker image can be used that runs both `check.py` and `assemble.py`:
```bash
docker run -v $(pwd):/app thisisnttheway/anki-deck-compiler:latest <host:port> <folder>
# The Anki directory must be mounted into /app  
```

### Folder structure
The script expects the following folder structure:
```bash
anki
├── assets (OPTIONAL)
│   ├── image.png
│   └── audio.mp3
├── card
│   ├── back.html
│   ├── front.html
│   └── style.css
├── config.yaml
└── decks
    ├── Subdeck 1.csv
    └── Subdeck 2.csv
```

The following files and folders are of interest
- `assets`
  - Media files used in the deck.
  - Optional and only used if `webserver: true` is set in `config.yaml`
- `card`
  - Card template definitions.
- `decks`
  - CSV files of decks.
    Each file gets rendered into its own subdeck, with the file name being name of the deck.
- `config.yaml`
  - Contains deck information such as master deck name, model name and note fields.

### Deck config
The file `/anki/config.yaml` must at minimum contain the following:
```yaml
masterDeckName: test_deck
modelName: test_model
modelNameDescriptive: test_model
fields:
 - question
 - answer
```

_`masterDeckName` is the name of the deck under which all subdecks (`/anki/decks/*.csv`) will be stored._

### CSVs
CSVs represent subdecks and contain notes.  
They must follow this structure:

```csv
field1;field2
My question 1;My answer 1
My question 2;My answer 2
My question 3;My answer 3
```

> [!WARNING]  
> CSVs **must** use the `;` delimiter.  
> Only fields that are specified in `config.yaml` will be included in notes.  
> Unknown fields will be ignored.

#### Media
To add pictures/audio, create new fields containing either `image` or `audio` in their name (case insensitive).  
For example, the following field names will create an **audio** field:  
- `Audio`
- `AudioSentence`
- `sentenceAudio`
- `auxilliaryaudio`
- `audio_word`

In the CSV, add URLs containing the respective media.  
AnkiConnect will then use this URL to download the asset:

```csv
image_fieldX;audio_fieldY
https://ex.com/example.jpg;https://ex.com/example.mp3
```

> [!NOTE]
> The script will check URLs before downloading them.  
> If the URL does not respond or does not return a media type, then the field gets skipped in the note.  
> This behaviour can be changed in `config.yaml` (shown are the defaults):
```yaml
urlCheck:
  # Enable URL check
  enabled: true
  # Timeout, in seconds, of URL check
  timeout: 1
```

> [!TIP] 
> If media only exists locally, a local webserver can be launched by setting `webserver: true` in `config.yaml`.  
> Port `1233` will be used by default, although this can be overridden using `webserverPort: <int>`.  
> Assets stored in `./anki/assets` are then served at `http://<ip>:1233/<file.suffix>`.  
> Note that the listen address is `0.0.0.0`.


#### Tags
To add tags to notes, add them into the field `tags` in a CSV.  
Tags are separated using `,`.

> [!NOTE]
> It is not necessary to add `tags` to the fields in `config.yaml`.
> Additionally, whitespaces will be stripped.  