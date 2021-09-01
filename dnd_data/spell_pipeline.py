from re import sub
import requests
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy.orm import relationship

if os.path.exists("dnd5e.db"):
    os.remove("dnd5e.db")
engine = create_engine("sqlite:///dnd5e.db", echo=True, future=True)
# "sqlite+pysqlite:///:memory:"


class SpellApi:
    def __init__(self, api_url=None):
        self.api_url = api_url

    def api_to_df(self):
        spells_list = []
        try:
            url_list = []
            for page in range(1, 8):
                spell_api_url = f"https://api.open5e.com/spells/?page={page}"
                url_spell_data = requests.get(spell_api_url, timeout=10)
                url_spell_data.raise_for_status()  # raise exception for error codes
                url_spell_data = url_spell_data.json()
                url_list.append(url_spell_data)
        except requests.exceptions.HTTPError as HTTP_err:
            raise SystemExit(HTTP_err)
        except requests.exceptions.ConnectionError as connect_err:
            print(f"Connection Error: {connect_err}")
        except requests.exceptions.Timeout as time_err:
            print(f"Timeout Error: {time_err}")
        except requests.exceptions.RequestException as err:
            print(f"Other Failure: {err}")
            raise SystemExit(err)
        else:
            spells_list = [
                pg_result for url_data in url_list for pg_result in url_data["results"]
            ]
            spells_df = self.api_spell_configuration(spells_list)
        return spells_df

    def api_spell_configuration(self, spells_list):
        spell_df = pd.DataFrame(spells_list)
        spell_df.drop(
            ["document__title", "document__license_url"], axis=1, inplace=True
        )

        return spell_df


def spell_explode_classes(df):
    spell_cls_df = pd.DataFrame(
        df["dnd_class"].str.split(",").tolist(), index=df["slug"]
    ).stack()
    spell_cls_df = spell_cls_df.to_frame().reset_index().copy()
    spell_cls_df.drop(["level_1"], axis=1, inplace=True)
    spell_cls_df.columns = ["slug", "class"]
    spellcasting_ability = {
        "Bard": "Charisma",
        "Cleric": "Wisdom",
        "Druid": "Wisdom",
        "Paladin": "Charisma",
        "Ranger": "Wisdom",
        "Sorcerer": "Charisma",
        "Warlock": "Charisma",
        "Wizard": "Intellegence",
    }

    spell_cls_df["cast_ability"] = spell_cls_df["class"].map(spellcasting_ability)

    return spell_cls_df


def spell_table(df):
    df = df[["slug", "desc"]].copy()
    subtable_df = df[df["desc"].str.contains("###")].copy()
    subtable_df["desc_table"] = df["desc"].str.split("|").str[1:-1]

    return subtable_df


spells_df = SpellApi().api_to_df()
spell_n_classes = spell_explode_classes(spells_df)
subtables = spell_table(spells_df)
print(len(spells_df))

##SQLAlchemy##

mapper_registry = registry()


@mapper_registry.mapped
class Spell:
    __tablename__ = "spells_of_api"

    id = Column(Integer, primary_key=True)
    slug = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    higher_level = Column(String)
    page = Column(String)
    spell_range = Column(String)
    components = Column(String)
    material = Column(String)
    ritual = Column(String)  # bool?
    duration = Column(String)
    concentration = Column(String)  # bool?
    casting_time = Column(String)
    level = Column(String)
    level_int = Column(Integer)
    school = Column(String)
    dnd_classes = Column(String)
    archetype = Column(String)
    circles = Column(String)

    dnd_class = relationship("SpellClasses", back_populates="spell_slug")


@mapper_registry.mapped
class SpellClasses:
    __tablename__ = "classes_of_spells_of_api"

    id = Column(Integer, primary_key=True)
    spell_id = Column(ForeignKey("spells_of_api.id"), nullable=False)
    dnd_class = Column(String, nullable=False)
    casting_ability = Column(String)

    spell_slug = relationship("Spell", back_populates="dnd_class")


with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)

Session = sessionmaker(bind=engine, future=True)


with Session.begin() as session:
    # spells_list = df.to_dict('records')
    spells_list = spells_df.to_dict("records")
    session.add_all([Spell(**spell_dict) for spell_dict in spells_list])
