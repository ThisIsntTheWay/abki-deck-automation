# Anki deck automation
This repo provides tools to automatically build and export an Anki deck.  
Will require an active AnkiConnect instance.

## Usage
To assemble a deck, execute `assemble.py`:
```bash
assemble.py <anki_folder> <deck_export_path> <host>
```
- `<host>` is the AnkiConnect instance and must be specified as `<ip>:<port>`.
- `<deck_export_path>` is the absolute path of the exported deck file.

_Additionally, the validity of the `anki` folder can be checked by running `check.py <folder>`._

As an alternative, a docker image can be used that runs both `check.py` and `assemble.py`:
```bash
docker run -v $(pwd):/opt thisisnttheway/anki-deck-compiler:latest <host:port> <anki_folder> <anki_export_path>
# Containerized, the script expects <anki_folder> at /opt
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
    - Assuming `singleDeck: False` in `config.yaml`
- `config.yaml`
  - Contains deck information such as master deck name, model name and note fields.

### Deck config
The file `/anki/config.yaml` must at minimum contain the following:
```yaml
masterDeckName: test_deck
modelName: test_model
fields:
 - question
 - answer
```

- `masterDeckName`
  - Name of the (master) deck under which all subdecks will be stored under.
- `models`
  - Array of models to create in Anki.
  - Each entry must have the keys `name` and `fields[]`.

#### Single deck
By default, the script will create subdecks using all the CSV files under `/anki/decks/*.csv`.  
If `singleDeck: true` is set in the `config.yaml`, the script will instead create a single deck with the name `masterDeckName`.  
In this case, the script will only consume the CSV file `main.csv`.

### CSVs
CSVs represent subdecks and contain notes.  
They are assembled as such:

```csv
question;answer;picture
My question 1;My answer 1;https://ex.com/red.png
My question 2;My answer 2;https://ex.com/green.png
My question 3;My answer 3;https://ex.com/blue.png
```

> [!WARNING]  
> By default, the script assumes the `;` delimiter.  
> To change this, set `csvDelimiter` in the `config.yaml` to a different value.  
> Only fields that are specified in `config.yaml` will actually be included in notes, apart from `tags` (See below).

#### Media
To add pictures/audio, create new fields containing either `image` or `audio` in their name (case insensitive).  
For example, the following field names would create an **audio** field:  
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
> This behaviour can be changed in `config.yaml` (shown are the defaults if not specified otherwise):

```yaml
urlCheck:
  # Enable URL check
  enabled: true
  # Timeout, in seconds, of URL check
  timeout: 1
```

##### Local media
If media only exists locally, a webserver can be launched that serves all files under `./anki/assets`.  
The webserver can be configured in the `config.yaml` as such (shown are the defaults if not specified otherwise):  

```yaml
webserver:
  # Enable webserver
  enabled: true
  # Listen port
  port: 1233
  # Listen address
  listenAddress: 0.0.0.0
```

Assets can the be accessed at `http://<ip>:<port>/<file>`.  
(E.g. `http://localhost:1233/file.mp3`)

#### Tags
To add tags to notes, add them into the field `tags` in a CSV.  
Tags are separated using `,`.

> [!NOTE]
> It is not necessary to add `tags` to the fields in `config.yaml`.  
> Additionally, whitespaces will be stripped.  
