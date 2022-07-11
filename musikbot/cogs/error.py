import discord
import wavelink
from discord.ext import commands

from musikbot.classes.exceptions import NotInSameVoiceChannel, NotInVoiceChannel, QueueIsEmpty, NoMoreTracks, \
    NoPreviousTracks, VolumeTooLow, VolumeTooHigh, PlayerIsAlreadyPaused, AlreadyConnectedToChannel, NoVoiceChannel, \
    PlaylistToBig


class ErrorCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, NotInSameVoiceChannel):
            await ctx.respond("You need to be in the Same VoiceChannel as the Bot!", hidden=True)
        elif isinstance(exc, NotInVoiceChannel):
            await ctx.respond("Bot is not playing in any VoiceChannel!", hidden=True)
        elif isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.", hidden=True)
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("There are no more tracks in the queue.", hidden=True)
        elif isinstance(exc, NoPreviousTracks):
            await ctx.response("There are no previous tracks in the queue.", hidden=True)
        elif isinstance(exc, VolumeTooLow):
            await ctx.respond("The volume must be 0% or above.", hidden=True)
        elif isinstance(exc, VolumeTooHigh):
            await ctx.respond("The volume must be 150% or below.", hidden=True)
        elif isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.respond("Already paused.", hidden=True)
        elif isinstance(exc, AlreadyConnectedToChannel):
            await ctx.respond("Already connected to a voice channel.", hidden=True)
        elif isinstance(exc, NoVoiceChannel):
            await ctx.respond("No suitable voice channel was provided.", hidden=True)
        elif isinstance(exc, PlaylistToBig):
            await ctx.respond("The given Playlist is to big", hidden=True)
        elif isinstance(exc, wavelink.LoadTrackError):
            await ctx.respond("Error when loading the Playlist! It could be that your playlist is private!")
        else:
            raise exc

    @commands.Cog.listener()
    async def on_application_command_error(self, cmd, ctx, exc):
        if isinstance(exc, NotInSameVoiceChannel):
            await ctx.respond("You need to be in the Same VoiceChannel as the Bot!", hidden=True)
        elif isinstance(exc, NotInVoiceChannel):
            await ctx.respond("Bot is not playing in any VoiceChannel!", hidden=True)
        elif isinstance(exc, QueueIsEmpty):
            await ctx.respond("This could not be executed as the queue is currently empty.", hidden=True)
        elif isinstance(exc, NoMoreTracks):
            await ctx.respond("There are no more tracks in the queue.", hidden=True)
        elif isinstance(exc, NoPreviousTracks):
            await ctx.response("There are no previous tracks in the queue.", hidden=True)
        elif isinstance(exc, VolumeTooLow):
            await ctx.respond("The volume must be 0% or above.", hidden=True)
        elif isinstance(exc, VolumeTooHigh):
            await ctx.respond("The volume must be 150% or below.", hidden=True)
        elif isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.respond("Already paused.", hidden=True)
        elif isinstance(exc, AlreadyConnectedToChannel):
            await ctx.respond("Already connected to a voice channel.", hidden=True)
        elif isinstance(exc, NoVoiceChannel):
            await ctx.respond("No suitable voice channel was provided.", hidden=True)
        elif isinstance(exc, PlaylistToBig):
            await ctx.respond("The given Playlist is to big", hidden=True)
        # elif isinstance(exc, wavelink.LoadTrackError):
        #    await ctx.respond("Error when loading the Playlist! It could be that your playlist is private!")
        else:
            raise exc


def setup(bot):
    bot.add_cog(ErrorCog(bot))
