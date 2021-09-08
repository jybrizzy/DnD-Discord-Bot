from abc import ABC, abstractmethod
import json
import pandas as pd
import os

cwd = os.getcwd()
pd.set_option("display.max_columns", None)
print(cwd)

from collections import OrderedDict
from sqlalchemy.orm import sessionmaker, aliased
from cogs.utils.spell_orm_mapper import engine, Spell, SpellClasses


class DnDPipeline(ABC):
    def __init__(self):
        self.df = None
        self.fin_dictionary = None

    @abstractmethod
    def init_df(self):
        pass

    @abstractmethod
    def process_df(self):
        pass

    @abstractmethod
    def df_to_dictionary(self):
        pass


class SpellJsonPipeline(DnDPipeline):
    # "spell_json_directory"
    def init_df(self, json_reference):
        with open(".\\config.json", "r") as config_json:
            config = json.load(config_json)

        spell_dir = config[json_reference]

        with open(spell_dir) as spell_json_file:
            spell_json = json.loads(spell_json_file.read())

        self.df = pd.DataFrame(spell_json)
        return self

    def process_df(self):
        self.df.rename(columns={"classes": "dnd_classes"}, inplace=True)
        self.df["slug"] = self.df["name"].str.strip().str.replace(" ", "-").str.lower()
        self.df["higher_levels"] = self.df["higher_levels"].fillna("")
        self.df["level_int"] = (
            self.df["level"].where(self.df["level"].str.isnumeric(), 0).astype(int)
        )
        self.df["components"] = [
            components.get("raw") for components in self.df["components"]
        ]

        self.df = self.df[
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
            ]
        ].copy()

        return self

    def df_to_dictionary(self):
        # df_to_dictionary needs to be called after "dnd_classes" column is referenced.
        self.df.drop("dnd_classes", axis=1, inplace=True)
        spell_slug = self.df["slug"].unique().tolist()
        spells_list = self.df.to_dict(into=OrderedDict, orient="records")
        spell_insts = [Spell(**spell_dict) for spell_dict in spells_list]
        self.fin_dictionary = OrderedDict(list(zip(spell_slug, spell_insts)))
        return self.fin_dictionary


class ClassesOfSpell(DnDPipeline):
    CASTING_ABILITY = {
        "Bard": "Charisma",
        "Cleric": "Wisdom",
        "Druid": "Wisdom",
        "Paladin": "Charisma",
        "Ranger": "Wisdom",
        "Sorcerer": "Charisma",
        "Warlock": "Charisma",
        "Wizard": "Intellegence",
    }

    def init_df(self, parent_df):
        self.df = (
            pd.DataFrame(
                parent_df["dnd_classes"]
                .apply(lambda clst: [ent.strip().title() for ent in clst])
                .tolist(),
                index=parent_df["slug"],
            )
            .stack()
            .to_frame()
        )
        return self

    def process_df(self):
        self.df.index = self.df.index.rename(None, level=0)
        self.df["slug"] = self.df.index.get_level_values(0)
        self.df.columns = ["dnd_class", "slug"]
        self.df = self.df.reindex(columns=["slug", "dnd_class"], copy=True)

        self.df["cast_ability"] = self.df["dnd_class"].map(self.CASTING_ABILITY)
        return self

    def df_to_dictionary(self):
        self.fin_dictionary = OrderedDict(
            [
                (spell, self.df.xs(spell).to_dict("records"))
                for spell in self.df.index.levels[0]
            ]
        )
        return self.fin_dictionary


spell_obj = SpellJsonPipeline().init_df("spell_json_directory").process_df()
spell_class_dict = (
    ClassesOfSpell().init_df(parent_df=spell_obj.df).process_df().df_to_dictionary()
)
spell_dict = spell_obj.df_to_dictionary()


Session = sessionmaker(bind=engine, future=True)


with Session.begin() as session:
    for slug, spelldb_obj in spell_dict.items():
        class_per_spell = spell_class_dict.get(slug, [])
        spelldb_obj.dnd_class = [
            SpellClasses(**spell_class) for spell_class in class_per_spell
        ]
    session.add_all(list(spell_dict.values()))
