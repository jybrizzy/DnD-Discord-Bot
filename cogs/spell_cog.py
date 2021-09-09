import discord
from discord.ext import commands
import DiscordUtils
import re

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from cogs.utils.spell_orm_mapper import engine, Spell, SpellClasses


Session = sessionmaker(bind=engine, future=True)
session = Session()


class SpellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready to Cast!")

    @commands.command(name="cast", aliases=("spell_lookup"))
    async def _cast(self, ctx, *, magic_word: str):
        try:
            # transform spell to slug
            magic_word = magic_word.lower().strip()
            MAGIC_WORD = re.sub(r"\s+", "_", magic_word)

            result = session.execute(select(Spell).filter_by(slug=MAGIC_WORD))
            spell_rlt = result.scalars().one()

        except Exception as e:
            print(e)


class SpellBook:
    def __init__(self, ctx, spell):
        self.ctx = ctx
        self.spell = spell
        self.embed = None

    def spell_embedder(self):
        self.embed = discord.Embed(
            title=self.spell.name,
            description=self.spell.description,
            color=0x109319,
        )

        self.embed.add_field(name="Type", value=self.spell.type, inline=False)
        self.embed.add_field(
            name="Casting Time", value=self.spell.casting_type, inline=False
        )
        self.embed.add_field(name="Range", value=self.spell.range, inline=False)
        self.embed.add_field(
            name="Components", value=self.spell.components, inline=False
        )
        self.embed.add_field(name="Duration", value=self.spell.duration, inline=False)
        self.embed.add_field(name="Classes", value=self.spell.dnd_classes, inline=False)
        """
        self.embed.add_field(
            name="Description", value=self.spell.description, inline=False
        )
        """
        if self.spell.higher_levels:
            self.embed.add_field(
                name="At Higher Levels",
                value=self.spell.higher_levels,
                inline=False,
            )
