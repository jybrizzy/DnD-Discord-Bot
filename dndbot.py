import discord
from discord.ext import commands
from random import randint
import os
import json

with open(".\\config.json", "r") as con_json:
    config = json.load(con_json)

PREFIX = config["prefix"]
DESCRIPTION = """ """


bot = commands.Bot(command_prefix=PREFIX, description=DESCRIPTION)


@bot.event
async def on_ready():
    print("Kahinga!")
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


@bot.command()
async def load_cogs(ctx, extension):
    bot.load_extension(f"cogs.{extension}")


@bot.command()
async def unload_cogs(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")


if __name__ == "__main__":
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")

    bot.run(config["token"])
