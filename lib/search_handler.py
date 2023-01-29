# Python 3 Core Libraries

# Python 3 Third Party Libraries


# Python 3 Project Libraries
import os
import random
import subprocess
import uuid

import cv2
import requests
from colorama import Fore, Style
from youtubesearchpython import *
import wikipedia as wiki

from lib.database_handler import Database
from lib.feature_status_handler import FeatureStatus
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin


class Search:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.MAGENTA + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.GREEN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s == prefix + "search":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["search_status"] == 1:
                status = 0
            else:
                status = 1
            FeatureStatus(self).set_feature_status(chat_message, status, "search_status")
        elif s == prefix + "search status":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]

            if group_settings["search_status"] == 1:
                status_string = "Search Status: On\n"
            else:
                status_string = "Search Status: Off\n"

            RemoteAdmin(self).send_message(chat_message, status_string)
        elif s[:3] == prefix + "yt" or s[:8] == "youtube":
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]

            if group_settings["search_status"] == 1:
                RemoteAdmin(self).send_message(chat_message, "Searching....")
                search_term = chat_message.body[9:]
                fetcher = StreamURLFetcher()
                video_search = VideosSearch(search_term, limit=4, language='en', region='US')
                search_list = video_search.result()
                count = len(search_list["result"])
                selection = random.randint(0, count - 1)

                link = search_list["result"][selection]["link"]
                vid_dur = search_list["result"][selection]["duration"].split(":")[0]
                if int(vid_dur) > 5:
                    RemoteAdmin(self).send_message(chat_message, "Video too long.")
                    return
                video = Video.get(link)
                url = fetcher.get(video, 18)
                vid_id = uuid.uuid4()
                vid = requests.get(url, stream=True)
                if vid.status_code == 200:
                    with open(self.config["paths"]["youtube_media"] + str(vid_id) + "_temp.mp4", 'wb') as f:
                        for chunk in vid.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                        f.close()
                    thumbnail = self.config["paths"]["youtube_media"] + str(vid_id) + ".jpg"
                    video = self.config["paths"]["youtube_media"] + str(vid_id) + "_temp.mp4"
                    command_thumb = "ffmpeg -i {} -ss 00:00:02.000 -vframes 1 {}".format(video, thumbnail)
                    command_compress = "ffmpeg -i {} -vcodec libx264 -crf 20 -vf scale=256:144 {}".format(video,
                                                                                                          self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4")

                    result = subprocess.run(
                        # Command as a list, to avoid shell=True
                        command_thumb.split(),
                        # Expect textual output, not bytes; let Python .decode() on the fly
                        text=True,
                        # Shorthand for stdout=PIPE stderr=PIPE etc etc
                        capture_output=True,
                        # Raise an exception if ping fails (maybe try/except it separately?)
                        check=True)
                    result2 = subprocess.run(
                        # Command as a list, to avoid shell=True
                        command_compress.split(),
                        # Expect textual output, not bytes; let Python .decode() on the fly
                        text=True,
                        # Shorthand for stdout=PIPE stderr=PIPE etc etc
                        capture_output=True,
                        # Raise an exception if ping fails (maybe try/except it separately?)
                        check=True)
                    dur = cv2.VideoCapture(self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4")
                    duration = dur.get(cv2.CAP_PROP_POS_MSEC)
                    file_size = os.path.getsize(self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4")
                    if file_size > 14900000:
                        RemoteAdmin(self).send_message(chat_message, "Video too big.")
                        os.remove(video)
                        os.remove(self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4")
                        os.remove(self.config["paths"]["youtube_media"] + str(vid_id) + ".jpg")
                        return
                    self.client.send_chat_video(chat_message.group_jid, self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4",
                                                thumbnail, duration)
                    os.remove(video)
                    os.remove(self.config["paths"]["youtube_media"] + str(vid_id) + ".mp4")
                    os.remove(self.config["paths"]["youtube_media"] + str(vid_id) + ".jpg")
            else:
                RemoteAdmin(self).send_message(chat_message, "Searches are off.")
        elif prefix + "who" in s:
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]
            if group_settings["search_status"] == 1:
                search_term = chat_message.body[6:]
                if len(search_term.split()) > 4:
                    RemoteAdmin(self).send_message(chat_message, "Name is to long.")
                try:
                    answer = wiki.summary(search_term, sentences=2)
                    RemoteAdmin(self).send_message(chat_message, answer)
                except Exception as e:
                    RemoteAdmin(self).send_message(chat_message,
                                                  'Too many articles found. Be more specific.')

            else:
                RemoteAdmin(self).send_message(chat_message, "Searches are off.")
        elif prefix + "urban" in s:
            group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
            group_settings = group_data["group_settings"]

            if group_settings["search_status"] == 1:
                search_term = chat_message.body[4:]
                url = "http://api.urbandictionary.com/v0/define?term=" + search_term

                result = requests.get(url)
                if result.status_code == 200:
                    answers = result.json()
                    answer_list = []
                    count = 0
                    for a in answers["list"]:
                        answer_list.append(count)
                        count += 1
                    choice = random.choice(answer_list)
                    RemoteAdmin(self).send_message(chat_message, answers["list"][choice]["definition"])
                else:
                    RemoteAdmin(self).send_message(chat_message, "Try again later.")

            else:
                RemoteAdmin(self).send_message(chat_message, "Searches are off.")


