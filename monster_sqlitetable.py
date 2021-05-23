import json
import sqlite3
from sqlite3 import Error
import pandas as pd

pd.set_option("display.max_columns", None)

# Image File: https://github.com/matnad/paperminis/blob/master/monsters.json
DB_FILE = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\dnd.db"
JSON_DIR = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\json_folders\\"
JSON_FILE = {
    "base_monsters_5e": "monsters_base5e.json",
    "monsters_images": "monsters_images.json",
    "monsters_TomeofBeasts": "monsters_TomeofBeasts.json",
}
