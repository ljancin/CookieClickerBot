## Requirements
* Python 3.10
* Google Chrome

## Install and run
```
pip install -r requrements.txt
python main.py
```

# Saves
Saves are stored in the ```saves``` folder. By default, each save is denoted by its start time.
Loading saved games or starting a new game can be controlled through the config file.

## Config
./cookie_clicker_bot/config.json

* SAVE
    * ```"LAST"``` - loads last saved game. Creates new save if none exist.
    * ```null``` - starts a new game every time.
    *  ```[save_folder]``` - loads a save with the specified name.
