import discord
from discord import ActionRow, SelectMenu, SelectOption, ApplicationCommandInteraction as APPCI
from discord.ext import commands
import wavelink

from musikbot.classes.equalizer import Equalizer
from musikbot.classes.exceptions import AlreadyConnectedToChannel, NoVoiceChannel, NoTracksFound, QueueIsEmpty
import datetime
from musikbot.classes.playlists import CustomPlaylist
import asyncio
from musikbot.classes.queue import Queue

OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.eq: Equalizer = Equalizer.from_equalizer('flat')

    async def getcurrenttrack(self):
        return self.queue.current_track

    async def teardown(self):
        try:
            await self.stop()
            await self.disconnect()
        except KeyError:
            pass

    async def add_tracks(self, ctx: APPCI, tracks):
        if not tracks:
            raise NoTracksFound
        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
            await ctx.respond(
                f"Added {len(tracks.tracks)} Songs from `{tracks.data['playlistInfo']['name']}` to to the Queue",
                hidden=True, components=[])
        elif isinstance(tracks, CustomPlaylist):
            self.queue.add(*tracks.tracks)
            title = "title"
            await ctx.respond(
                f"Added {len(tracks.tracks)} Songs {f'from `{tracks.data.get(title)}` ' if tracks.data.get(title) else ''}to to the Queue",
                hidden=True, components=[])
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.respond(f"Added {tracks[0].title} to the queue.", hidden=True, components=[])
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                await ctx.respond(f"Added```{track.title}``` to the queue.",hidden=True)
        if not self.is_playing() and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks: list[wavelink.Track]):
        def _check(r, u):
            return (
                    r.emoji in OPTIONS.keys()
                    and u == ctx.author
                    and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i + 1}.** {t.title} ({t.length // 60000}:{str(t.length % 60).zfill(2)})"
                    for i, t in enumerate(tracks[:8])
                )
            ),
            colour=ctx.author.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        components = ActionRow(
            SelectMenu(options=[
                SelectOption(label=f"{i + 1}. {t.title}"[:99],
                             description=f"({t.length // 60000}:{str(t.length % 60).zfill(2)}) {t.author}",
                             value=str(i)) for i, t in enumerate(tracks[:24])],
                custom_id="785062348890",
                placeholder="select a song",
                max_values=1,
                min_values=1)
        )
        trackstochoose = {}
        msg = await ctx.respond(embed=embed, components=[components], hidden=True)

        # for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
        #   await msg.add_reaction(emoji)

        try:
            hello, select = await ctx.bot.wait_for("selection_select", check=lambda c, select: (
                c.author == ctx.author, ctx.guild == c.guild, c.channel == ctx.channel, ctx.author != self.user),
                                                   timeout=60)

            # reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await ctx.respond("You Waited to long! Time is over now!", hidden=True)
        else:
            hello: discord.ComponentInteraction = hello
            select: SelectMenu = select
            await hello.defer()
            if str(select.custom_id) == "785062348890":
                return tracks[int(str(select.values[0]))]

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def play_track(self, track):
        self.queue.add(track)
        await self.play(track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
                return True
            else:
                return False
        except QueueIsEmpty:
            return False

    async def repeat_track(self):
        await self.play(self.queue.current_track)


"""
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel
"""
