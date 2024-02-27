import yaml
import os
import csv
import re
import platform
import requests
import json
import argparse
from urllib.parse import urlparse, unquote
from pathlib import Path
from termcolor import colored
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

# -----------------
# GLOBALS
parser = argparse.ArgumentParser()

parser.add_argument("folder", help="Anki folder", nargs="?", default="anki")
parser.add_argument("export_path", help="Absolute path of deck export", nargs="?", default="/export/export.apkg")
parser.add_argument("host", help="AnkiConnect host", nargs="?", default="localhost:8765")
args = parser.parse_args()

anki_card_config_basepath = args.folder
anki_decks_path = f"{anki_card_config_basepath}/decks"
single_deck_master_file = "main.csv"

with open(f"{anki_card_config_basepath}/config.yaml", "r") as stream:
    deck_config = yaml.safe_load(stream)
    
if platform.system().lower() == 'windows':
    os.system('color')

# -----------------
# FUNCTIONS
def start_http_server(port, listen_address, directory):
    """Launch an HTTP webserver

    Args:
        port (int): Listen port
        listen_address (string): Listen address
        directory (string): Serving directory
    """
    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    def run_server():
        try:
            server_address = (listen_address, port)
            httpd = HTTPServer(server_address, CustomHandler)
            print(colored(f"[i] Webserver enabled, listening on: {listen_address}:{port}", 'cyan'))
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
        except Exception as e:
            print(colored(f"Webserver serving error: {e}", 'red'))
            raise SystemExit(str(e))

    # Start the server in a separate thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
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

    is_single_deck = deck_config.get("singleDeck", False)
    deckName = name if is_single_deck else f"{deck_config['masterDeckName']}::{name}"
    
    request = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deckName
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
                    "Name": deck_config["modelName"],
                    "Front": anki_card_formats[0],
                    "Back": anki_card_formats[1]
                }
            ]
        }
    }
    
    return request

def create_notes_request(target_csv, target_deck):
    """Creates notes

    Args:
        target_csv (string): Path of CSV containing note data
        target_deck (string): Name of target deck
    """
    
    path = f"{anki_decks_path}/{target_csv}"
    delimiter = deck_config.get("csvDelimiter", ";")
    
    with open(path, newline='') as file:
        csv_data = csv.DictReader(file, delimiter=delimiter)
        
        notes_array = []
        for row in csv_data:            
            fields_obj = {}
            for field in deck_config["fields"]:
                # Skip fields with no value or ones that contain media
                is_media = re.search(field, 'picture', re.IGNORECASE) or re.search(field, 'audio', re.IGNORECASE)
                if row[field] is not None and not is_media:
                    fields_obj[field] = row[field]
                
            # Handle tags and media
            media_body = []
            tags = []
            for k, v in row.items():
                if re.search(k, 'picture', re.IGNORECASE) or re.search(k, 'audio', re.IGNORECASE):
                    if v is not None:
                        try:
                            # Check if media is accessible
                            if deck_config["urlCheck"]["enabled"]:
                                timeout = deck_config["urlCheck"]["timeout"]
                                media_request_content_type = requests.head(v, timeout=timeout).headers.get('content-type')
                                if not media_request_content_type.startswith('image') and not media_request_content_type.startswith("audio"):
                                    raise Exception(f"Content type '{media_request_content_type}' inacceptable for media")
                        
                            media_type = k.split("_")[0]
                            url_filename = os.path.basename(unquote(urlparse(v).path))
                            media_body.append({
                                "url": v,
                                "filename": url_filename,
                                "fields": [k]
                            })
                            
                        except Exception as e:
                            print(colored(f"[X]   > Not able to download '{v}': {str(e)}", 'red'))
                elif re.search(k, 'tags', re.IGNORECASE):
                    if v is not None:
                        tags = v.strip().split(",")
            
            note_body = {
                "deckName": target_deck,
                "modelName": deck_config["modelName"],
                "fields": fields_obj
            }
            
            if len(tags) > 0:
                note_body["tags"] = tags
            
            if len(media_body) > 0:
                note_body[media_type] = media_body
            
            notes_array.append(note_body)
    
    request = {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": notes_array
        }
    }
    
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
    url = f"http://{args.host}"
    
    # Webserver
    if "webserver" in deck_config.keys():
        if deck_config["webserver"].get("enabled", True):
            port = deck_config["webserver"].get("port", 1233)
            listen_address = deck_config["webserver"].get("listenAddress", "0.0.0.0")
            start_http_server(port, listen_address, os.path.join(os.getcwd(), "anki", "assets"))

    print(colored('[?] Checking for AnkiConnect permissions...', 'yellow'))
    if not do_i_have_perms(url):
        print(colored('[X] Not permitted.', 'red'))
        raise SystemExit("AnkiConnect does not grant permissions to the client.")
    else:
        print(colored('[i] Permissions have been granted.', 'green'))

    # Iterate through all decks
    decks = [f for f in os.listdir(anki_decks_path) if os.path.isfile(os.path.join(anki_decks_path, f))]

    # Create base data
    print(colored('[+] Creating base data...', 'yellow'))
    model_request = create_model_request()
    answer = requests.post(url, json = model_request)

    answer_error = answer.json()["error"]
    if answer_error is not None:
        if not "name already exists" in answer_error:
            raise Exception(f"Error creating model: {answer_error}")
        
    # Deck options
    is_single_deck = deck_config.get("singleDeck", False)
    master_deck_name = deck_config['masterDeckName']

    if is_single_deck:
        print(colored('[i] singleDeck is set to true. Deck will be saved as', 'cyan'), master_deck_name)
        if not single_deck_master_file in decks:
            err_msg = f"Deck file {single_deck_master_file} was not found."
            print(colored(f"[X] {err_msg}", 'red'))
            raise FileNotFoundError(err_msg)

    for deck in decks:
        this_deck_name = Path(deck).stem
        deck_name = master_deck_name if is_single_deck else f"{master_deck_name}::{this_deck_name}"

        print(colored('[i] Processing deck:', 'cyan'), deck, colored(f"({deck_name})", 'yellow'))
        try:
            print(colored('[+] > Creating deck...', 'yellow'))
            requests.post(url, json = create_deck_request(deck_name))
            
            print(colored('[+] > Creating notes...', 'yellow'))
            answer = requests.post(url, json = create_notes_request(deck, deck_name))
            
            amount_bad = answer.json()["result"].count(None)
            if amount_bad > 0:
                print(colored(f"[X]  > {amount_bad} notes were not created.", 'red'))
                #raise Exception("Not all notes created")
        except Exception as e:
            raise SystemExit(str(e))
        
        if is_single_deck:
            break
            
    print(colored(f"[i] Exporting deck to '{args.export_path}'", 'cyan'))
    answer = requests.post(url, json = create_deck_export_request(deck_config["masterDeckName"], args.export_path))

    if answer.json()["result"]:
        print(colored('[i] All done.', 'green'))
    else:
        print(colored('[i] Export failed:', 'red'), answer.json())
        raise SystemExit("Export failed")
    
if __name__ == "__main__":
    main()
