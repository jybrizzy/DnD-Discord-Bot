import discord
from discord.ext import commands
import DiscordUtils
import sqlite3
from sqlite3 import Error
import numpy as np
import pandas as pd
import re


class SpellBook:
    def __init__(
        self,
        ctx,
        spellbook_df,
    ):
        self.ctx = ctx
        self.spellbook_df = spellbook_df
        self.spellbook_dict = dict()
        self.embed_dict = dict()

    @property
    def spell_embedder(self):

        self.spellbook_dict = self.spellbook_df.to_dict("index")
        for pg_num, (spell_name, spell_info) in enumerate(self.spellbook_dict.items()):
            self.embed_dict[f"pg{pg_num}"] = discord.Embed(
                title=spell_name,
                description=spell_info["description"],
                color=0x109319,
            )

            # int(hex(int("42d7f5", 16)), 0)

            embed_page = self.embed_dict[f"pg{pg_num}"]
            embed_page.add_field(name="Type", value=spell_info["type"], inline=False)
            embed_page.add_field(
                name="Casting Time", value=spell_info["casting_time"], inline=False
            )
            embed_page.add_field(name="Range", value=spell_info["range"], inline=False)
            embed_page.add_field(
                name="Components", value=spell_info["components"], inline=False
            )
            embed_page.add_field(
                name="Duration", value=spell_info["duration"], inline=False
            )
            embed_page.add_field(
                name="Classes", value=spell_info["classes"], inline=False
            )
            """
            embed_page.add_field(
                name="Description", value=spell_info["description"], inline=False
            )
            """
            if str(spell_info["higher_levels"]) != "":
                embed_page.add_field(
                    name="At Higher Levels",
                    value=spell_info["higher_levels"],
                    inline=False,
                )
            # embed_page.set_footer(text=spell_info["description"])

        return self.embed_dict


class SpellCog(commands.Cog):

    spell_classes = (
        "Bard",
        "Cleric",
        "Druid",
        "Paladin",
        "Ranger",
        "Sorcerer",
        "Warlock",
        "Wizard",
    )

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready to Cast!")

    def queue_database(self):
        try:
            dnd_cnx = sqlite3.connect(self.DB_FILE)
            return dnd_cnx
        except Error as e:
            return print(f"Something went wrong: {e}")

    def spell_by_lvl(self, level):
        level_bull = [f"• {spell}" for spell in level]
        return "\n  ".join("{}".format(spell_name) for spell_name in level_bull)

    @commands.command(name="cast")
    async def _cast(self, ctx, *, magic_word: str):
        try:
            magic_word = magic_word.strip()
            dnd_cnx = self.queue_database()
            spellname_qry = f"""SELECT 
                                    * 
                                FROM 
                                    spells_5e 
                                WHERE 
                                    name 
                                LIKE 
                                    "{magic_word}" 
                                LIMIT 1"""

            spell_df = pd.read_sql_query(spellname_qry, dnd_cnx)

            if len(spell_df) == 0:
                return await ctx.send("This spell does not appear in the spellbook!")

            # spell = spell_df.to_dict("records")[0]
            # .to_dict("records") -> [{'col1': value1, 'col2': value2}]
            spell_df.set_index(["name"], inplace=True)
            spell_embed_dict = SpellBook(ctx, spell_df).spell_embedder
            spell_pg = list(spell_embed_dict.values())[0]
            await ctx.send(embed=spell_pg)

        except Exception as e:
            print(e)

    @commands.command(name="class_spell_list", aliases=())
    async def class_lvl_book(self, ctx, *, cls_n_lvl: str):

        cls_n_lvl = re.sub(r"\s+", "", cls_n_lvl, flags=re.UNICODE)
        cls_raw, lvl_raw = cls_n_lvl.split(":")
        pattern = r"cantrip|\d"
        try:
            if match := re.search(pattern, lvl_raw, re.IGNORECASE):
                spell_lvl = match.group(0)
        except ValueError as valerr:
            print(valerr)
            await ctx.send("Not a valid spell level")

        class_search = cls_raw.title()
        if class_search not in self.spell_classes:
            await ctx.send("Not a valid spell level")
            raise ValueError("Class is not in represented in spell library")
        dnd_cnx = self.queue_database()

        spell_book_qry = f"""
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

        lvl_spells_df = pd.read_sql_query(spell_book_qry, dnd_cnx)
        lvl_spells_df["class"] = class_search
        lvl_spells_df.set_index(["name"], inplace=True)
        spell_book_embed = SpellBook(ctx, lvl_spells_df).spell_embedder
        paginator = DiscordUtils.Pagination.AutoEmbedPaginator(ctx)
        embeds = list(spell_book_embed.values())
        await paginator.run(embeds)

    @commands.command(name="spells", aliases=("spells_of", "class_spells"))
    async def class_spells(self, ctx, _class: str):
        if _class.lower().strip() not in (
            "bard",
            "cleric",
            "druid",
            "paladin",
            "ranger",
            "sorcerer",
            "warlock",
            "wizard",
        ):
            raise ValueError("Class is not in represented in spell library")
        dnd_cnx = self.queue_database()
        _class = _class.title().strip()
        classlist_qry = f"""SELECT
                        name, level, classes, school, ritual 
                    FROM 
                        spells_5e 
                    WHERE 
                        classes LIKE "%{_class}%" ORDER BY level, name;"""

        cls_spells_df = pd.read_sql_query(classlist_qry, dnd_cnx)
        cls_spells_df["class"] = _class
        level, spell_names = cls_spells_df[["level", "name"]].values.T
        ulvl, index = np.unique(level, return_index=True)
        array_spells = np.split(spell_names, index[1:])
        lvl_dict = dict(zip(list(ulvl), [list(ar) for ar in array_spells]))

        cls_lvls_str = list(ulvl)
        try:
            cls_lvls_str.remove("cantrip")

        except ValueError:
            pass
        except AttributeError as error:
            print(f"Wait, seems we can't do that: {error}")
            # Logging.log_exception(error)

        cls_lvls = list(map(int, cls_lvls_str))
        # ordinal = lambda n: f'{n}{"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]}'

        cls_spell = discord.Embed(
            title=f"**{_class}**",
            description=f"Spell Casting Ability: {self.spellcasting_ability[_class]}",
            color=ctx.author.color,
        )
        """
        PHOTO_FILE = discord.File(
            f".\\class_icons\\{cls_proper}.png", filename=f"{cls_proper}.png"
        )
        cls_spell.set_thumbnail(url=f"attachment://{cls_proper}.png")
        """
        if "cantrip" in lvl_dict:
            cls_spell.add_field(
                name="Cantrip",
                value=self.spell_by_lvl(lvl_dict["cantrip"]),
                inline=True,
            )
        for lvl in range(np.min(cls_lvls), np.max(cls_lvls) + 1):
            # ordinal = lambda n: f'{n}{"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]}'
            # lvl = ordinal(str(lvl))
            cls_spell.add_field(
                name=f"Spell Level {lvl}",
                value=self.spell_by_lvl(lvl_dict[str(lvl)]),
                inline=True,
            )

        # await ctx.send(file=PHOTO_FILE, embed=cls_spell)
        await ctx.send(embed=cls_spell)


def setup(bot):
    bot.add_cog(SpellCog(bot))


"""
@_cast.error
async def cast_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify a spell.")

            spell_pg = discord.Embed(
                title=spell["name"], description=spell["type"], color=ctx.author.color
            )
            # spell_pg.set_author(name=spell["name"])
            spell_pg.add_field(
                name="Casting Time", value=spell["duration"], inline=False
            )
            spell_pg.add_field(name="Range", value=spell["range"], inline=False)
            spell_pg.add_field(
                name="Components", value=spell["components"], inline=False
            )
            spell_pg.add_field(name="Duration", value=spell["duration"], inline=False)
            spell_pg.add_field(name="Classes", value=spell["classes"], inline=False)
            spell_pg.add_field(
                name="Description", value=spell["description"], inline=False
            )
            if str(spell["higher_levels"]) != "":
                spell_pg.add_field(
                    name="At Higher Levels", value=spell["higher_levels"], inline=False
                )

"""
