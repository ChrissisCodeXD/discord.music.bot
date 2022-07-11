import math
from musikbot.classes.Google import Create_Service
from pprint import pprint
from googleapiclient.discovery import Resource


class utils:
    CLIENT_SECRET_FILE = 'F:\jetbrains\projects\discord.music.bot\musikbot\classes\client-secret.json'
    API_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    def __init__(self, logger):
        self.service: Resource = Create_Service(self.CLIENT_SECRET_FILE, self.API_NAME, self.API_VERSION, self.SCOPES,
                                                logger=logger)

    def get_data(self, track_id):

        data = self.service.videos().list(
            part='contentDetails,statistics,snippet',
            id=track_id
        ).execute()
        data2 = self.service.channels().list(
            part='contentDetails,statistics,snippet',
            id=data['items'][0]['snippet']['channelId']
        ).execute()
        toret = {
            'author_url': f"https://www.youtube.com/channel/{data['items'][0]['snippet']['channelId']}",
            'author_icon_url': data2['items'][0]['snippet']['thumbnails']['high']['url'],
            'video_views': data['items'][0]['statistics']['viewCount'],
            'video_commentcount': data['items'][0]['statistics']['commentCount'],
            'video_likecount': data['items'][0]['statistics']['likeCount']
        }
        return toret

    @staticmethod
    def convertSec(secs):
        hours = math.floor(secs / 3600)
        secs = secs - (hours * 3600)
        minutes = math.floor(secs / 60)
        secs = secs - (minutes * 60)
        hours = str(hours) if len(str(hours)) == 2 else "0" + str(hours)
        minutes = str(minutes) if len(str(minutes)) == 2 else "0" + str(minutes)
        seconds = str(secs) if len(str(secs)) == 2 else "0" + str(secs)
        return f"{hours}:{minutes}:{seconds}"

    @staticmethod
    def positionbuilder(position, lenth):
        current = int(round(position / lenth, 1) * 25)
        toreturn = ""
        for i in range(0, 25):
            if i == current:
                toadd = "⬤"
            elif i < current:
                toadd = "━"
            else:
                toadd = "─"
            toreturn += toadd
        return toreturn

    @staticmethod
    def volumebuilder(volume):
        current = int(round(volume / 150, 1) * 45)
        toreturn = ""
        for i in range(0, 45):
            if i == current:
                toadd = "⬤"
            elif i < current:
                toadd = "━"
            else:
                toadd = "─"
            toreturn += toadd
        return toreturn
