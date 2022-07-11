import logging
from pathlib import Path

import discord
from discord.ext import commands


class MusikBot(commands.Bot):

    def __init__(self, logger: logging.Logger, *args, **kwargs):
        self.logger: logging.Logger = logger
        self._cogs = [p.stem for p in Path("../musikbot/cogs/").glob("*.py")]
        self.logger.info(str(self._cogs))
        self._prefix = kwargs.get("prefix")
        super().__init__(
            command_prefix=self.prefix(),
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_id=589898942527963157,
            sync_commands=True
        )

    def setup(self):
        self.logger.info("Running Setup")

        for cog in self._cogs:
            self.load_extension("musikbot.cogs." + cog)
            self.logger.info(f" Loaded `{cog}` cog")

        self.logger.info("Setup Complete")

    def prefix(self):
        return commands.when_mentioned_or(self._prefix or ".!")

    def run(self):
        # with open("data/token.0", "r", encoding="utf-8") as f:
        #    TOKEN = f.read()
        self.setup()
        self.logger.debug("Running bot...")
        # self.ipc.start()
        TOKEN = "Dachtet Ihr nh"
        super().run(TOKEN, reconnect=True)

    async def on_ready(self):
        self.logger.critical(
            f"https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=8&scope=bot%20applications.commands")
