import json
import requests
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

# MONSTER_API_URL = "https://api.open5e.com/monsters/?armor_class=&challenge_rating=&document=&document__slug=wotc-srd&name=&ordering=challenge_rating&page=1&type="

try:
    url_list = []
    for pg_num in range(1, 8):
        monster_api_url = f"https://api.open5e.com/monsters/?armor_class=&challenge_rating=&document=&document__slug=wotc-srd&name=&ordering=challenge_rating&page={pg_num}&type="
        url_monst_data = requests.get(monster_api_url, timeout=5)
        url_monst_data.raise_for_status()
        url_monst_data = url_monst_data.json()
        url_list.append(url_monst_data)
except requests.exceptions.HTTPError as HTTP_err:
    raise SystemExit(HTTP_err)
except requests.exceptions.ConnectionError as connect_err:
    print(f"Connection Error: {connect_err}")
except requests.exceptions.Timeout as time_err:
    print(f"Timeout Error: {time_err}")
except requests.exceptions.RequestException as err:
    print(f"Catostrophic Failure: {err}")
    raise SystemExit(err)
else:
    page_list = []
    for url_data in url_list:
        page_df = pd.DataFrame(url_data["results"])
        page_list.append(page_df)

raw_monster_df = pd.concat(page_list)
print(len(page_list))