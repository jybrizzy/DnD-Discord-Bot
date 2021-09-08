import os
from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import registry, relationship

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
    higher_levels = Column(String)
    range = Column(String)
    components = Column(String)
    # material = Column(String)
    ritual = Column(Boolean)
    duration = Column(String)
    # concentration = Column(String)
    casting_time = Column(String)
    level = Column(String)
    level_int = Column(Integer)
    school = Column(String)
    dnd_classes = Column(String)
    type = Column(String)
    # add: find PHB page

    dnd_class = relationship("SpellClasses", back_populates="spell")


@mapper_registry.mapped
class SpellClasses:
    __tablename__ = "classes_of_spells"

    id = Column(Integer, primary_key=True)
    spell_id = Column(ForeignKey("spells_of_json.id"), nullable=False)
    slug = Column(String, nullable=False)
    dnd_class = Column(String, nullable=False)
    cast_ability = Column(String)

    spell = relationship("Spell", back_populates="dnd_class")


with engine.begin() as connection:
    mapper_registry.metadata.create_all(connection)
