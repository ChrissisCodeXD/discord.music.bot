import asyncio
import logging
import re
import datetime

from discord.ext import commands
import discord
import wavelink
from wavelink import Track
from wavelink.ext import spotify
from musikbot.classes.enums import RepeatMode
from musikbot.classes.playlists import CustomPlaylist
from musikbot.classes.equalizer import Equalizer
from discord import ComponentInteraction, SlashCommandOption, SlashCommandOptionChoice, OptionType, \
    ApplicationCommandInteraction as APPCI, Permissions, ActionRow, Button, SelectMenu, SelectOption

from musikbot.classes.exceptions import AlreadyConnectedToChannel, NoVoiceChannel, QueueIsEmpty, PlayerIsAlreadyPaused, \
    NotInVoiceChannel, NotInSameVoiceChannel, NoMoreTracks, NoPreviousTracks, InvalidRepeatMode, VolumeTooLow, \
    VolumeTooHigh
from musikbot.classes.player import Player
from musikbot.classes.searcher import Searcher
from musikbot.classes.utils import utils


class _EmptyEmbed:
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Embed.Empty'

    def __len__(self):
        return 0


EmptyEmbed = _EmptyEmbed()


class Musik(commands.Cog):
    GUILD_IDS = [764397934476263464]
    URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    CLIENT_ID = "4ade69c1befe40ac9c0ca48aa9f6a3f6"
    CLIENT_SECRET = "330bdc53cd164b3db94c2475036bbc8c"

    def __init__(self, bot):
        self.bot = bot
        self.node = None
        self.bot.loop.create_task(self.connect_nodes())
        self.playlistLimit = 300
        self.searcher = None
        self.l: logging.Logger = self.bot.logger
        self.u: utils = utils(self.l)

    @commands.Cog.slash_command("test", guild_ids=GUILD_IDS)
    async def test(self, ctx):
        await ctx.defer(hidden=True)
        await ctx.respond("test", hidden=True, components=[ActionRow(SelectMenu("asddsadasdas",
                                                                                [SelectOption("test1", "test1"),
                                                                                 SelectOption("test2", "test2"),
                                                                                 SelectOption("test3", "test3"),
                                                                                 SelectOption("test4", "test4")]))])
        await asyncio.sleep(2)
        await ctx.respond("test2", hidden=True, components=[])

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        self.bot.logger.info("Connecting Nodes...")
        await self.bot.wait_until_ready()

        self.node: wavelink.Node = await wavelink.NodePool.create_node(
            bot=self.bot,
            host='45.129.183.230',
            port=8123,
            password='youshallnotpass',
            spotify_client=spotify.SpotifyClient(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET
            )
        )
        self.searcher: Searcher = Searcher(self.node, self.playlistLimit)

        self.bot.logger.info("Connected Nodes...")

    def get_player(self, obj):
        if isinstance(obj, commands.Context) or isinstance(obj, APPCI) or isinstance(obj, ComponentInteraction):
            return self.node.get_player(obj.guild)
        elif isinstance(obj, discord.Guild):
            return self.node.get_player(obj)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("logged in")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node):
        self.bot.logger.info(f"Wavelink node `{node.identifier}` ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: Player, track: Track | wavelink.YouTubeTrack):
        if isinstance(player.channel, discord.VoiceChannel):
            channel_url = None
            video_views = None
            author_icon = None
            if track.uri.__contains__("youtube"):
                track = await self.node.get_tracks(wavelink.YouTubeTrack, track.uri)
                track: wavelink.YouTubeTrack = track[0]
            if track.identifier and track.uri.__contains__("youtube"):
                data = self.u.get_data(track.identifier)
                channel_url = data['author_url']
                video_views = data['video_views']
                author_icon = data['author_icon_url']
            embed = discord.Embed(title="New Song is playing!", url=track.uri, colour=discord.Colour.green(),
                                  timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Song", value=f"[{track.title}]({track.uri})")
            if video_views:
                embed.add_field(name="Views", value=str(video_views))
            if track.author:

                embed.set_author(name=track.author)
                if channel_url:
                    embed.set_author(name=track.author,
                                     url=channel_url
                                     )
                elif channel_url and author_icon:
                    embed.set_author(name=track.author,
                                     url=channel_url,
                                     icon_url=author_icon
                                     )
                elif author_icon:
                    embed.set_author(name=track.author,
                                     icon_url=author_icon
                                     )

            if track.length:
                embed.add_field(name="Position",
                                value=f"```diff\n{self.u.convertSec(int(player.position))} {self.u.positionbuilder(player.position, track.length)}  {self.u.convertSec(int(track.length))}```",
                                inline=False)
            if player.volume:
                embed.add_field(name="Volume",
                                value=f"```fix\n{self.u.volumebuilder(player.volume)} {player.volume}```",
                                inline=False)
            if (thumb := getattr(track, "thumbnail", None)) is not None:
                embed.set_image(url=thumb)

            await player.channel.send(embed=embed)

    async def timeout_after(self, time, player):
        await asyncio.sleep(time)
        player = self.get_player(player.guild)
        if player and not player.is_playing():
            await player.channel.send(embed=discord.Embed(title="I left the Voice Channel",
                                                          description=f"I did not played songs for 15 minutes so i decidet to leave the channel."))
            await player.teardown()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player, track, reason):
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            stillplaying = await player.advance()
            if not stillplaying:
                self.bot.loop.create_task(self.timeout_after(60 * 15, player))
                if isinstance(player.channel, discord.VoiceChannel):
                    embed = discord.Embed(title="Stopped Playing!",
                                          description="There are no more tracks in the Queue so i stopped playing. I will leave the Voice Channel in 15 Minutes!")
                    await player.channel.send(embed=embed)
            #    await self.EmbedClear(payload.player.guild_id)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, player, payload, threshold):
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            stillplaying = await player.advance()
            if not stillplaying:
                self.bot.loop.create_task(self.timeout_after(60 * 15, player.guild))
                if isinstance(player.channel, discord.VoiceChannel):
                    embed = discord.Embed(title="Stopped Playing!",
                                          description="There are no more tracks in the Queue so i stopped playing. I will leave the Voice Channel in 15 Minutes!")
                    await player.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, player, payload, error):
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            stillplaying = await player.advance()
            if not stillplaying:
                self.bot.loop.create_task(self.timeout_after(60 * 15, player.guild))
                if isinstance(player.channel, discord.VoiceChannel):
                    embed = discord.Embed(title="Stopped Playing!",
                                          description="There are no more tracks in the Queue so i stopped playing. I will leave the Voice Channel in 15 Minutes!")
                    await player.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                try:
                    await self.get_player(member.guild).teardown()
                except AttributeError as e:
                    pass
        if member.id == self.bot.user.id and after.channel is None:
            try:
                await self.get_player(member.guild).teardown()
            except AttributeError as e:
                pass

    @commands.Cog.slash_command(name="join", description="This will make tho Bot join your Voice Channel",
                                guild_ids=GUILD_IDS,
                                options=[
                                    SlashCommandOption(name="channel",
                                                       description="The Channel the Bot should connect to",
                                                       option_type=OptionType.channel, required=False)
                                ])
    async def _join_command(self, ctx, channel=None):
        channel = channel or ctx.author.voice.channel
        if not channel.type == discord.ChannelType.voice:
            raise NoVoiceChannel()
        player: Player = self.get_player(ctx)
        if player and player.channel:
            raise AlreadyConnectedToChannel()
        vc = await channel.connect(cls=Player)
        await ctx.respond(f"Connected to {channel.name}", hidden=True)

    @commands.Cog.slash_command(name="leave", description="This will make tho Bot leave your Voice Channel",
                                guild_ids=GUILD_IDS)
    async def _disconnect_command(self, ctx):
        player: Player = self.get_player(ctx)
        await player.teardown()
        await ctx.respond("Disconnected.", hidden=True)

    @commands.Cog.slash_command(name="play", description="This will make tho Bot play something in your Voice-Channel",
                                guild_ids=GUILD_IDS, options=[
            SlashCommandOption(name="song", description="The Song you want to play",
                               option_type=OptionType.string, required=True)
        ])
    async def play_command(self, ctx: APPCI, song=None):
        await ctx.defer(hidden=True)

        player = self.get_player(ctx)

        if not player or not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                raise NoVoiceChannel()
            elif not ctx.author.voice.channel.type == discord.ChannelType.voice:
                raise NoVoiceChannel()
            else:
                await ctx.author.voice.channel.connect(cls=Player)

        player: Player = self.get_player(ctx)

        if song is None:
            if player.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            await ctx.respond("Playback resumed.", hidden=True)

        else:
            query = song.strip("<>")

            if query.startswith("https://open.spotify.com"):
                ret = spotify.decode_url(query)["type"]
                if ret == spotify.SpotifySearchType.track:
                    track = [await spotify.SpotifyTrack.search(query=query, return_first=True)]
                    await player.add_tracks(ctx, track)
                elif ret == spotify.SpotifySearchType.album:
                    tracks = await spotify.SpotifyTrack.search(query=query)
                    await player.add_tracks(ctx, tracks)
                elif ret == spotify.SpotifySearchType.playlist:
                    tracks = spotify.SpotifyTrack.iterator(query=query, partial_tracks=True)
                    tracks = CustomPlaylist([track async for track in tracks])
                    await player.add_tracks(ctx, tracks)
            elif query.startswith("https://soundcloud.com"):
                query = await self.searcher.searchSoundcloud(ctx, query)
                if query is None:
                    return
                else:
                    await player.add_tracks(ctx, query)
            elif query.startswith("https://deezer.page.link") or query.startswith("https://www.deezer.com"):
                query = await self.searcher.searchDeezer(ctx, query)
                if query is None:
                    return
                else:
                    await player.add_tracks(ctx, query)
            elif not re.match(self.URL_REGEX, query):
                await ctx.respond("Loading Songs please wait!", delete_after=3)
                query = f"ytsearch:{query}"
                await player.add_tracks(ctx, await self.node.get_tracks(wavelink.YouTubeTrack, query))
            elif re.match(self.URL_REGEX, query):
                await ctx.respond("Loading Songs please wait!", delete_after=3)
                await player.add_tracks(ctx, await self.node.get_tracks(wavelink.YouTubeTrack, query))

    @commands.Cog.slash_command(name="pause", description="This will make tho Bot pause the Current Music",
                                guild_ids=GUILD_IDS)
    async def pause_command(self, ctx):
        player = self.get_player(ctx)
        if player and player.is_paused():
            raise PlayerIsAlreadyPaused
        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()

        await player.set_pause(True)
        await ctx.respond("Playback paused.", hidden=True)

    @commands.Cog.slash_command(name="stop", description="This will make tho Bot stop the Current Music",
                                guild_ids=GUILD_IDS)
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()
        player.queue.empty()
        await player.stop()
        await ctx.respond("Playback stopped.", hidden=True)

    @commands.Cog.slash_command(name="skip", description="This will make tho Bot skip the Current Song",
                                guild_ids=GUILD_IDS)
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()
        if not player.queue.upcoming:
            raise NoMoreTracks()

        await player.stop()
        await ctx.response("Playing next track in queue.", hidden=True)

    @commands.Cog.slash_command(name="previous", description="This will make tho Bot play the Previous Song",
                                guild_ids=GUILD_IDS)
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()
        if not player.queue.history:
            raise NoPreviousTracks()

        player.queue.position -= 2
        await player.stop()
        await ctx.response("Playing previous track in queue.", hidden=True)

    @commands.Cog.slash_command(name="shuffle", description="This will make the Bot shuffle the Current Queue",
                                guild_ids=GUILD_IDS)
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()
        player.queue.shuffle()
        await ctx.respond("Queue shuffled.", hidden=True)
        # await self.updateEmbed(player=player, currentTrack=player.queue.current_track)

    @commands.Cog.slash_command(name="repeat", description="This will make tho Bot repeat a Song or Playlist",
                                guild_ids=GUILD_IDS, options=[
            SlashCommandOption(name="mode", description="Select the Repeatmode!", option_type=OptionType.string,
                               choices=[
                                   SlashCommandOptionChoice(value="none", name="None"),
                                   SlashCommandOptionChoice(value="1", name="Current Song"),
                                   SlashCommandOptionChoice(value="all", name="Queue")
                               ], required=True)
        ])
    async def repeat_command(self, ctx, mode: str):
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = self.get_player(ctx)
        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()
        player.queue.set_repeat_mode(mode)
        await ctx.respond(f"The repeat mode has been set to {mode}.", hidden=True)

    @commands.Cog.slash_command(name="queue", description="This will make the Bot show the next x Tracks in the Queue",
                                guild_ids=GUILD_IDS, options=[
            SlashCommandOption(name="anzahl", description=f"Wieviele Songs sollen gezeigt werden?",
                               option_type=OptionType.integer, required=False)
        ])
    async def queue_command(self, ctx, anzahl=10):
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Queue",
            description=f"Showing up to next {anzahl} tracks",
            colour=ctx.author.colour,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(
            name="Currently playing",
            value=getattr(player.queue.current_track, "title", "No tracks currently playing."),
            inline=False
        )
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Next up",
                value="\n".join(t.title for t in upcoming[:anzahl]),
                inline=False
            )

        msg = await ctx.respond(embed=embed, hidden=True)

    @commands.Cog.slash_command(name="volume", description="This will change the Bots volume", guild_ids=GUILD_IDS,
                                options=[
                                    SlashCommandOption(name="volume", description=f"Volume",
                                                       option_type=OptionType.integer, required=False, min_value=0,
                                                       max_value=150)
                                ])
    async def volume_command(self, ctx, volume: int):
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()

        if volume < 0:
            raise VolumeTooLow

        if volume > 150:
            raise VolumeTooHigh

        await player.set_volume(volume)
        await ctx.respond(f"Volume set to {volume}%", hidden=True)
        # await self.updateEmbed(player=player, currentTrack=player.queue.current_track)

    @commands.Cog.slash_command(name="equalizer", description="This will change the Bots equalizer",
                                guild_ids=GUILD_IDS,
                                options=[
                                    SlashCommandOption(name="eqtype", description="Type of the EQ you want to set",
                                                       option_type=str, required=True, choices=[
                                            SlashCommandOptionChoice(name=Equalizer.EQUALIZERS[i]["name"], value=i)
                                            for i in Equalizer.EQUALIZERS
                                        ])
                                ])
    async def equalizer_command(self, ctx, eqtype: str):
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()

        eq = Equalizer.from_equalizer(
            eqtype
        )

        eqq = wavelink.Equalizer(name=eq.name,
                                 bands=eq.bands)

        await player.set_filter(
            wavelink.Filter(
                equalizer=eqq
            )
        )
        player.eq = eq

        await ctx.respond(f"EQ is now set to {eq.name}", hidden=True)


    @commands.Cog.slash_command(name="customeq", description="Settings for a Custom eq",
                                guild_ids=GUILD_IDS,
                                options=[
                                    SlashCommandOption(name="band", description="which band of the eq you wanna edit", option_type=int, required=True, choices=[
                                        SlashCommandOptionChoice(name=i, value=Equalizer.HZ_BANDS[i])
                                        for i in Equalizer.HZ_BANDS
                                    ]),
                                    SlashCommandOption(name="gain", description="how much gain",
                                                       option_type=str, required=True, choices=[
                                            SlashCommandOptionChoice(name=i, value=str(i))
                                            for i in Equalizer.GAINS
                                    ])
                                ])
    async def custom_equalizer_command(self, ctx, band: int,gain: str):
        if not band:
            band = 0
        player = self.get_player(ctx)

        if not player:
            raise NotInVoiceChannel()
        if not ctx.author.voice or not player.channel == ctx.author.voice.channel:
            raise NotInSameVoiceChannel()

        if player.eq.is_default_eq:
            player.eq = Equalizer.from_equalizer('flat')

        gain = float(gain)
        player.eq.edit_bands({
            str(band): (int(band), float(gain))
        })
        eqq = wavelink.Equalizer(name=player.eq.name,
                                 bands=player.eq.bands)

        await player.set_filter(
            wavelink.Filter(
                equalizer=eqq
            )
        )

        await ctx.respond(f"EQ Band {list(Equalizer.HZ_BANDS)[band]} is now set to -> {gain}. The effect can take some seconds to apply.", hidden=True)







def setup(bot):
    bot.add_cog(Musik(bot))
