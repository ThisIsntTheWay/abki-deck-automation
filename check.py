import os
import platform
import argparse
from pathlib import Path
from termcolor import colored

if platform.system().lower() == 'windows':
    os.system('color')

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("path", help="Anki content folder", nargs="?", default="./anki")
    args = parser.parse_args()
    
    args_path_adjusted = args.path if not args.path.endswith("/") else args.path[:1]
    
    # Check if Anki folder has expected structure
    required_files = [
        "card/back.html",
        "card/front.html",
        "card/style.css",
        "config.yaml"
    ]
    
    missing_files = []
    for file in required_files:
        full_path = Path(f"{args_path_adjusted}/{file}")
        if not full_path.exists():
            missing_files.append(full_path)
            
    # Check decks directory
    decks_folder_ok = True
    decks_path = f"{args_path_adjusted}/decks"
    try:
        folder_contents = os.listdir(decks_path)
        if len(folder_contents) == 0:
            raise Exception("Decks folder is empty.")
        elif len([f for f in folder_contents if f.endswith('.csv')]) == 0:
            raise Exception("No decks exist.")
        
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            missing_files.append(decks_path)
        else:
            print(colored(f"[X] Problem with decks folder: {str(e)}", 'red'))
            
        decks_folder_ok = False

    missing_files_length = len(missing_files)
    if missing_files_length > 0 or not decks_folder_ok:
        plural = "s" if missing_files_length > 1 else ''
        
        print(colored(f"[X] Missing {missing_files_length} item{plural}:", 'red'))
        for missing_file in missing_files:
            print('   ', colored(missing_file, "yellow"))
        
        raise SystemExit("Anki folder does not contain all required files and/or folders.")
        
    print(colored('[i] Anki folder is valid.', 'green'))

if __name__ == "__main__":
    main()