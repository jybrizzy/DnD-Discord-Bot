from re import sub
import requests
import os
import pandas as pd
from collections import OrderedDict
from sqlalchemy import create_engine
from sqlalchemy import insert, select
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy.orm import relationship

if os.path.exists("dnd5e.db"):
    os.remove("dnd5e.db")
engine = create_engine("sqlite:///dnd5e.db", future=True)
# "sqlite+pysqlite:///:memory:"
# echo = True


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
        spells_df = pd.DataFrame(spells_list)
        spells_df.drop(
            ["document__title", "document__license_url"], axis=1, inplace=True
        )
        spells_df.rename(
            columns={"desc": "description", "dnd_class": "dnd_classes"},
            inplace=True,
            errors="raise",
        )
        # spells_df["higher_levels"] = spells_df["higher_levels"].fillna("")

        return spells_df


def spell_explode_classes(df):
    spell_cls_df = (
        pd.DataFrame(
            df["dnd_classes"]
            .str.split(",")
            .apply(lambda clst: [ent.strip() for ent in clst])
            .tolist(),
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


# def spell_table(df):
#     df = df[["slug", "desc"]].copy()
#     subtable_df = df[df["desc"].str.contains("###")].copy()
#     subtable_df["desc_table"] = df["desc"].str.split("|").str[1:-1]

#     return subtable_df


spells_df = SpellApi().api_to_df()
spll_cls = spell_explode_classes(spells_df)
clss_dict = OrderedDict(
    [
        (spell, spll_cls.xs(spell).to_dict("record"))
        for spell in spll_cls.index.levels[0]
    ]
)
# subtables = spell_table(spells_df)
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
    casting_ability = Column(String)

    spell = relationship("Spell", back_populates="dnd_class")


with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)

Session = sessionmaker(bind=engine, future=True)


def map_classes_to_spells(spell_dict, class_dict):
    for key, value in spell_dict.items():
        class_per_spell = class_dict.get(key, [])
        value.dnd_class = SpellClasses(**class_per_spell)


with Session.begin() as session:
    spell_slug = spells_df["slug"].unique().tolist()
    spells_list = spells_df.to_dict(into=OrderedDict, orient="records")
    spell_insts = [Spell(**spell_dict) for spell_dict in spells_list]
    spell_dictionary = OrderedDict(zip(spell_slug, spell_insts))
    map_classes_to_spells(spell_dictionary, clss_dict)
    session.add(list(spell_dictionary.values))

session = Session()

# single spell query
result = session.execute(select(Spell).filter_by(name="Augury"))
spell_rlt = result.scalars().one()

print(spell_rlt.name)

select(Spell)

## Spells of a class and level
"""
spell_book_qry = 
            SELECT *
            FROM 
                spells_5e 
            WHERE 
                classes LIKE "%{class_search}%"
            AND
                level LIKE "{spell_lvl}" 
            ORDER BY 
                name;

"""
##Spells of a class
stmt = (
    select(Spell.slug, Spell.name, Spell.level, SpellClasses.slug)
    .join(Spell.dnd_class)
    .where(SpellClasses.dnd_class == "Druid")
)
print(session.execute(stmt).all())
##Spells of a class and school of magic
