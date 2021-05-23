import json
import sqlite3
from sqlite3 import Error
import pandas as pd

pd.set_option("display.max_columns", None)


DB_FILE = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\dnd.db"
JSON_FILE = "C:\\Users\\jbrizzy\\Desktop\\DnD_DB\\json_folders\\spells.json"
# json from  vorpalhex/srd_spells on github

with open(JSON_FILE) as spell_file:
    spell_json = json.loads(spell_file.read())

spells_df = pd.DataFrame(spell_json)
spells_df["higher_levels"] = spells_df["higher_levels"].fillna("")

spells_df["classes"] = [
    ", ".join(map(str, cls_list)) for cls_list in spells_df["classes"]
]
spells_df["classes"] = spells_df["classes"].str.title()
spells_df["tags"] = [", ".join(map(str, tag_list)) for tag_list in spells_df["tags"]]

spells_df["components"] = [
    components.get("raw") for components in spells_df["components"]
]

spells_df["ritual"] = spells_df["ritual"].astype(int)


try:
    db_conn = sqlite3.connect(DB_FILE)
    spells_df.to_sql(name="spells_5e", con=db_conn, if_exists="replace")
    ###Test###
    cur = db_conn.cursor()
    cur.execute(
        """
    SELECT name, level, classes, school, ritual FROM spells_5e WHERE classes LIKE "%druid%" ORDER BY level, name;
    """
    )
    print(cur.fetchall())
    ###Test End###
    db_conn.commit()
    db_conn.close()
except Error as e:
    print(e)

# print(spells_df)

sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS spells_5e (
                                    id integer PRIMARY KEY,
                                    classes text collate noscase,
                                    components text,
                                    description text,
                                    duration text collate nocase,
                                    level text collate nocase,
                                    name text NOT NULL collate nocase,
                                    range text,
                                    ritual integer,
                                    school text collate nocase,
                                    tags text collate nocase,
                                    type text,
                                    higher_levels text
                                ); """
