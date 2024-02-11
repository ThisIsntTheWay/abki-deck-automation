## Building
To assemble a deck, execute `assemble.py`:
```bash
assemble.py <host> <deck_export_path>
```
- `<host>` is the AnkiConnect instance and must be specified as `<ip>:<port>`.
- `<deck_export_path>` is the absolute path of the exported deck file.

### Folder structure
The script expects the following folder structure:
```bash
anki
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
- `card`
  - Card template definitions.
- `decks`
  - CSV files of decks.
    Each file gets rendered into its own subdeck, with the file name being name of the deck.
- `config.yaml`
  - Contains deck information such as master deck name, model name and note fields.

### Deck config
The file `/anki/config.yaml` is expected to look like this:
```yaml
masterDeckName: test_deck
modelName: test_model
modelNameDescriptive: test_model
fields:
 - question
 - answer
```

`masterDeckName` is the name of the deck under which all subdecks (`/anki/decks/*.csv`) will be stored.

### CSVs
CSVs represent subdecks and contain notes.  
They must follow the following structure:
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

