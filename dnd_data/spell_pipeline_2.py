import json
import pandas as pd
import os
from collections import OrderedDict
from sqlalchemy import create_engine
from sqlalchemy import insert, select
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy.orm import relationship, aliased

cwd = os.getcwd()
pd.set_option("display.max_columns", None)
print(cwd)


class SpellJsonPipeline:
    def __init__(self):
        self.spells_df

    def json_to_df(self):
        with open(".\\config.json", "r") as config_json:
            config = json.load(config_json)

        spell_dir = config["spell_json_directory"]

        with open(spell_dir) as spell_json_file:
            spell_json = json.loads(spell_json_file.read())

        self.spells_df = pd.DataFrame(spell_json)
        return self

    def process_df(self):
        self.spells_df.rename(columns={"classes": "dnd_classes"}, inplace=True)
        self.spells_df["slug"] = (
            self.spells_df["name"].str.strip().str.replace(" ", "-").str.lower()
        )
        self.spells_df["higher_levels"] = self.spells_df["higher_levels"].fillna("")
        self.spells_df["level_int"] = (
            self.spells_df["level"]
            .where(self.spells_df["level"].str.isnumeric(), 0)
            .astype(int)
        )
        self.spells_df["components"] = [
            components.get("raw") for components in self.spells_df["components"]
        ]
        self.spells_df = self.spells_df[
            [
                "slug",
                "name",
                "description",
                "higher_levels",
                "range",
                "components",
                "ritual",
                "duration",
                "casting_time",
                "level",
                "level_int",
                "school",
                "dnd_classes",
                "type",
                "tags",
            ]
        ].copy()

        return self

    def df_to_dict(self):
        spell_slug = self.spells_df["slug"].unique().tolist()
        spells_list = self.spells_df.to_dict(into=OrderedDict, orient="records")
        spell_insts = [Spell(**spell_dict) for spell_dict in spells_list]
        self.spell_dictionary = OrderedDict(list(zip(spell_slug, spell_insts)))
        return self.spell_dictionary


def spell_explode_classes(df):
    spell_cls_df = (
        pd.DataFrame(
            df["dnd_classes"].apply(lambda clst: [ent.strip() for ent in clst]),
            index=df["slug"],
        )
        .stack()
        .to_frame()
    )

    spell_cls_df.index = spell_cls_df.index.rename(None, level=0)
    spell_cls_df["slug"] = spell_cls_df.index.get_level_values(0)
    spell_cls_df.columns = ["dnd_class", "slug"]
    spell_cls_df = spell_cls_df.reindex(columns=["slug", "dnd_class"], copy=True)
    spell_cls_df = spell_cls_df[~spell_cls_df["dnd_class"].isin(["Ritual Caster"])]
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

    spell_cls_df["cast_ability"] = spell_cls_df["dnd_class"].map(spellcasting_ability)

    return spell_cls_df


if os.path.exists("dnd5e.db"):
    os.remove("dnd5e.db")
engine = create_engine("sqlite:///dnd5e.db", future=True)

mapper_registry = registry()


@mapper_registry.mapped
class Spell:
    __tablename__ = "spells_of_json"

    id = Column(Integer, primary_key=True)
    slug = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    higher_level = Column(String)
    page = Column(String)
    range = Column(String)
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
    document__slug = Column(String)

    dnd_class = relationship("SpellClasses", back_populates="spell")


@mapper_registry.mapped
class SpellClasses:
    __tablename__ = "classes_of_spells_of_api"

    id = Column(Integer, primary_key=True)
    spell_id = Column(ForeignKey("spells_of_api.id"), nullable=False)
    slug = Column(String, nullable=False)
    dnd_class = Column(String, nullable=False)
    cast_ability = Column(String)

    spell = relationship("Spell", back_populates="dnd_class")


with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)

Session = sessionmaker(bind=engine, future=True)
