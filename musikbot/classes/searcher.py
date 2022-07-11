import wavelink
from musikbot.classes.exceptions import NoTracksFound, PlaylistToBig, InvalidDeezerTrack
from musikbot.classes.playlists import CustomPlaylist
import aiohttp
from discord import ApplicationCommandInteraction as APPCI


class Searcher:

    def __init__(self, node: wavelink.Node, limit: int = 300):
        self.node: wavelink.Node = node
        self.playlistLimit = limit

    async def searchSoundcloud(self, ctx: APPCI, args):
        """Get a YouTube link from a SoundCloud link."""
        track = await self.node.get_tracks(wavelink.SoundCloudTrack, args)
        if isinstance(track, wavelink.TrackPlaylist):
            if len(track) == 0:
                raise NoTracksFound
            elif len(track) > 1:
                if self.playlistLimit != 0 and len(track) > self.playlistLimit:
                    raise PlaylistToBig
                return track
        return track

    async def searchDeezer(self, ctx: APPCI, args):
        """Get a YouTube link from a Deezer link."""
        async with aiohttp.ClientSession() as session:
            async with session.get(args) as response:
                # Chack if it's a track
                if "track" in response._real_url.path:
                    link = await self.searchDeezerTrack(ctx, session, response)
                    if link is None: raise NoTracksFound
                    return [link]
                if "playlist" in response._real_url.path:
                    links = await self.searchDeezerPlaylist(ctx, session, response)
                    if links is None: raise NoTracksFound
                    return links
                raise InvalidDeezerTrack()

    async def searchDeezerTrack(self, ctx: APPCI, session, response):
        # Get the music ID
        trackId = response._real_url.name
        async with session.get(f"https://api.deezer.com/track/{trackId}") as response:
            response = await response.json()
            title = response["title_short"]
            artist = response["artist"]["name"]
            # Search on youtube
            track = await self.node.get_tracks(wavelink.YouTubeTrack, f'ytsearch:{title} {artist}')
            if len(track) == 0:
                raise NoTracksFound()
            return track[0]

    async def searchDeezerPlaylist(self, ctx: APPCI, session, response):
        # Get the playlist ID
        playlistId = response._real_url.name
        txt = f""
        async with session.get(f"https://api.deezer.com/playlist/{playlistId}") as response:
            response = await response.json()
            if self.playlistLimit != 0 and response["nb_tracks"] > self.playlistLimit:
                raise PlaylistToBig()
            await ctx.respond(
                f"Loading... (This process can take about {int(round(0.444 * response['nb_tracks'], 0))} seconds)",
                hidden=True,
                )
            trackLinks = []
            for i in response["tracks"]["data"]:
                title = i["title_short"]
                artist = i["artist"]["name"]
                # Search on youtube
                track = await self.node.get_tracks(wavelink.YouTubeTrack, f'ytsearch:{title} {artist}')
                if len(track) == 0:
                    if len(txt) == 0:
                        txt += f"{ctx.author.mention}\n"
                    txt += f"No song found for : `{title} - {artist}` ! \n"
                else:
                    trackLinks.append(track[0])
            if not trackLinks:
                raise NoTracksFound()
            if len(txt) != 0:
                await ctx.respond(txt, hidden=True)
            return CustomPlaylist(response, trackLinks)
