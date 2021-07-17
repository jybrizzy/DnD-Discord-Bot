import json
import requests
import sqlite3 as sq
from sqlite3 import Error
import pandas as pd

pd.set_option("display.max_columns", None)


class MonsterDataParser:
    # Image File: https://github.com/matnad/paperminis/blob/master/monsters.json
    DB_FILE = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\dnd.db"
    JSON_DIR = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\json_folders\\"
    JSON_FILE = {
        "monst_images": "monsters_images.json",
    }

    def __init__(self) -> None:
        self.url_list = []
        self.raw_monster_df = None
        self.img_df = None

    @property
    def api_to_df(self):
        try:
            for pg_num in range(1, 8):
                monster_api_url = f"https://api.open5e.com/monsters/?armor_class=&challenge_rating=&document=&document__slug=wotc-srd&name=&ordering=challenge_rating&page={pg_num}&type="
                url_monst_data = requests.get(monster_api_url, timeout=5)
                url_monst_data.raise_for_status()
                url_monst_data = url_monst_data.json()
                self.url_list.append(url_monst_data)
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
            for url_data in self.url_list:
                page_df = pd.DataFrame(url_data["results"])
                page_list.append(page_df)

        self.raw_monster_df = pd.concat(page_list, ignore_index=True, copy=True)
        self.raw_monster_df.set_index("name", inplace=True)
        return self.raw_monster_df

    @property
    def join_images(self):
        json_images = f"{self.JSON_DIR}{self.JSON_FILE['monst_images']}"
        with open(json_images) as monst_img:
            monster_img_json = json.loads(monst_img.read())
            self.image_df = pd.DataFrame.from_dict(monster_img_json, orient="index")

        self.raw_monster_df.join()
