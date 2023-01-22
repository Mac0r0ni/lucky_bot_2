import json
import time

from colorama import Fore, Style

from lib.message_processing_handler import MessageProcessing
from lib.redis_handler import RedisCache
from lib.trigger_handler import process_gif_sub


class GifResponse:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def parse_gif_response(self, response):
        # Gif Response
        if not response.group_jid:
            # PM GIF Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM GIF Response" + Style.RESET_ALL)

            remote_sessions = RedisCache(self.config).get_all_remote_sessions(self.bot_id)
            if response.from_jid.encode('utf-8') in remote_sessions:
                session_data = RedisCache(self.config).get_remote_session_data(response.from_jid, self.bot_id)
                response.remote_jid = response.from_jid
                response.group_jid = str(session_data["group_jid"]) + '@groups.kik.com'
                response.from_jid = session_data["user_ajid"]
                RedisCache(self.config).update_remote_session_data(response.from_jid, "last_activity", time.time(), self.bot_id)
                self.callback.on_gif_received(response)
        else:
            # Group GIF Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "Group GIF Response" + Style.RESET_ALL)

            group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
            if not group_data:
                return
            if "lurkers" in group_data and "talkers" in group_data:
                RedisCache(self.config).set_single_talker_lurker("talkers", time.time(), response.from_jid,
                                                                 response.group_jid)
                RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), response.from_jid,
                                                                 response.group_jid)
            else:
                if "group_members" in group_data:
                    RedisCache(self.config).add_all_talker_lurker("talkers", group_data["group_members"],
                                                                  response.group_jid)
                    RedisCache(self.config).add_all_talker_lurker("lurkers", group_data["group_members"],
                                                                  response.group_jid)
                    RedisCache(self.config).set_single_talker_lurker("talkers", time.time(), response.from_jid,
                                                                     response.group_jid)
                    RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), response.from_jid,
                                                                     response.group_jid)

            media_message_queue = RedisCache(self.config).get_all_media_message_queue(response.group_jid)
            for su in media_message_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(media_message_queue[su].decode('utf8'))
                    content = {}
                    preview_init = str(response.raw_element).split("<preview>")[1]
                    preview_final = preview_init.split("</preview>")[0]
                    content["preview"] = preview_final
                    content["mp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/mp4"
                    content["webm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/webm"
                    content["tinymp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/tinymp4"
                    content["tinywebm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanowebm"
                    content["nanomp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanomp4"
                    content["nanowebm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanowebm"
                    for x in response.uris:
                        uri = x.__dict__
                        if uri["file_content_type"] == "video/mp4":
                            content["mp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/webm":
                            content["webm"] = uri["url"]
                        elif uri["file_content_type"] == "video/tinymp4":
                            content["tinymp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/tinywebm":
                            content["tinywebm"] = uri["url"]
                        elif uri["file_content_type"] == "video/nanomp4":
                            content["nanomp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/nanowebm":
                            content["nanowebm"] = uri["url"]
                    if sub_data["response"][:2] == "$g":
                        MessageProcessing(self).process_gif_media(response, sub_data["type"],
                                          sub_data["response"], content,
                                          response.from_jid, response.group_jid)

            sub_queue = RedisCache(self.config).get_all_media_sub_queue(response.group_jid)
            for su in sub_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(sub_queue[su].decode('utf8'))
                    content = {}
                    preview_init = str(response.raw_element).split("<preview>")[1]
                    preview_final = preview_init.split("</preview>")[0]
                    content["preview"] = preview_final
                    content["mp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/mp4"
                    content["webm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/webm"
                    content["tinymp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/tinymp4"
                    content["tinywebm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanowebm"
                    content["nanomp4"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanomp4"
                    content["nanowebm"] = "https://media.riffsy.com/videos/7b1273371735f00dc052c0402b0b8f86/nanowebm"
                    for x in response.uris:
                        uri = x.__dict__
                        if uri["file_content_type"] == "video/mp4":
                            content["mp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/webm":
                            content["webm"] = uri["url"]
                        elif uri["file_content_type"] == "video/tinymp4":
                            content["tinymp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/tinywebm":
                            content["tinywebm"] = uri["url"]
                        elif uri["file_content_type"] == "video/nanomp4":
                            content["nanomp4"] = uri["url"]
                        elif uri["file_content_type"] == "video/nanowebm":
                            content["nanowebm"] = uri["url"]
                    if sub_data["response"][:2] == "$g":
                        process_gif_sub(self, response, sub_data["action"], sub_data["type"],
                                        sub_data["sub"], sub_data["response"], content,
                                        response.from_jid, response.group_jid)
