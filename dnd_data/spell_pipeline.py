import requests
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import registry
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
                url_spell_data = requests.get(spell_api_url, timeout=5)
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
        return spells_list


spells_list = SpellApi().api_to_df()
print(len(spells_list))


mapper_registry = registry()


@mapper_registry.mapped
class Spell:
    __tablename__ = "spell_api"

    id = Column(Integer, primary_key=True)
    slug = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    higher_level = Column(String)
    page = Column(String)
    spl_range = Column(String)
    components = Column(String)
    material = Column(String)
    ritual = Column(String)  # bool?
    duration = Column(String)
    concentration = Column(String)
    casting_time = Column(String)
    level = Column(String)
    level_int = Column(Integer)
    school = Column(String)
    dnd_class = Column(String)
