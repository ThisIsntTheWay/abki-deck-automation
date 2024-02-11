import yaml
import os
import csv
import platform
import requests
import json
import argparse
from pathlib import Path
from termcolor import colored

# -----------------
# GLOBALS
anki_card_config_basepath = "anki"
anki_decks_path = f"{anki_card_config_basepath}/decks"
with open(f"{anki_card_config_basepath}/config.yaml", "r") as stream:
    deck_config = yaml.safe_load(stream)
    
if platform.system().lower() == 'windows':
    os.system('color')

# -----------------
# FUNCTIONS
def do_i_have_perms(url):
    """Checks if client has permissions to call AnkiConnect

    Args:
        url (string): AnkiConnect URL

    Returns:
        bool: Whether or not the client is authorized to call the API
    """
    
    request = {
        "action": "requestPermission",
        "version": 6
    }
    
    answer = requests.post(url, json = request)
    return answer.json()["result"]["permission"] == "granted"

def create_deck_request(name):
    """Creates a deck

    Args:
        name (string): Name of the deck to create

    Returns:
        object: Request body for AnkiConneect
    """
    
    request = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": f"{deck_config["masterDeckName"]}::{name}"
        }        
    }
    
    return request

def create_model_request():
    """Creates a card model

    Returns:
        object: Request body for AnkiConneect
    """
    
    anki_card_format_files = [
       "front.html",
       "back.html",
       "style.css"
    ]
    
    anki_card_formats = []
    for anki_card_format_file in anki_card_format_files:
        with open(f"{anki_card_config_basepath}/card/{anki_card_format_file}") as file:
            anki_card_formats.append(file.read())
    
    request = {
        "action": "createModel",
        "version": 6,
        "params": {
            "modelName": deck_config["modelName"],
            "inOrderFields": deck_config["fields"],
            "css": anki_card_formats[2],
            "isCloze": False,
            "cardTemplates": [
                {
                    "Name": deck_config["modelNameDescriptive"],
                    "Front": anki_card_formats[0],
                    "Back": anki_card_formats[1]
                }
            ]
        }
    }
    
    return request

def create_notes_request(target_csv):
    """Creates notes

    Args:
        target_csv (string): Path of CSV containing note data
    """
    
    path = f"{anki_decks_path}/{target_csv}"
    
    deck_name = Path(path).stem
    with open(path, newline='') as file:
        csv_data = csv.DictReader(file, delimiter=';')
        
        notes_array = []
        for row in csv_data:
            fields_obj = {}
            for field in deck_config["fields"]:
                fields_obj[field] = row[field]
            
            note_body = {
                "deckName": f"{deck_config["masterDeckName"]}::{deck_name}",
                "modelName": deck_config["modelName"],
                "fields": fields_obj
            }
            
            notes_array.append(note_body)
    
    request = {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": notes_array
        }
    }
    
    f = open("notes_request_dump.json", "w")
    f.write(json.dumps(request))
    f.close()
    
    return request

def create_deck_export_request(deck_name, path, include_scheduling = False):
    """Exports an Anki deck

    Args:
        deck_name (string): Target deck to export
        path (string): Target path of deck export, absolute
        include_scheduling (bool): Include scheduling information

    Returns:
        dict: Request for AnkiConnect
    """
    
    request = {
        "action": "exportPackage",
        "version": 6,
        "params": {
            "deck": deck_name,
            "path": path,
            "includeSched": include_scheduling
        }
    }

    return request

# -----------------
# MAIN
def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("host", help="AnkiConnect host", nargs="?", default="localhost:8765")
    parser.add_argument("export_path", help="Absolute path of deck export", nargs="?", default="/export/export.apkg")
    args = parser.parse_args()
        
    url = f"http://{args.host}"

    print(colored('[?] Checking for AnkiConnect permissions...', 'yellow'))
    if not do_i_have_perms(url):
        print(colored('[X] Not permitted.', 'red'))
        raise SystemExit("AnkiConnect does not grant permissions to the client.")
    else:
        print(colored('[i] Permissions have been granted.', 'green'))

    # Iterate through all questions
    decks = [f for f in os.listdir(anki_decks_path) if os.path.isfile(os.path.join(anki_decks_path, f))]

    # Create base data
    print(colored('[+] Creating base data...', 'yellow'))
    model_request = create_model_request()
    requests.post(url, json = model_request)

    for deck in decks:
        print(colored('[i] Processing deck:', 'cyan'), deck)
        try:
            print(colored('[+] > Creating deck...', 'yellow'))
            requests.post(url, json = create_deck_request(Path(deck).stem))
            
            print(colored('[+] > Creating notes...', 'yellow'))
            answer = requests.post(url, json = create_notes_request(deck))
            
            amount_bad = answer.json()["result"].count(None)
            if amount_bad > 0:
                print(colored(f"[X]  > {amount_bad} notes were not created.", 'red'))
                #raise Exception("Not all notes created")
        except Exception as e:
            raise SystemExit(str(e))
            
    print(colored(f"[i] Exporting deck to '{args.export_path}'", 'cyan'))
    answer = requests.post(url, json = create_deck_export_request(deck_config["masterDeckName"], args.export_path))

    if answer.json()["result"]:
        print(colored('[i] All done.', 'green'))
    else:
        print(colored('[i] Export failed:', 'red'), answer.json())
        raise SystemExit("Export failed")
    
if __name__ == "__main__":
    main()