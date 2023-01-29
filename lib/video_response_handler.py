import json
import os
import time

from colorama import Fore, Style
import cv2

from lib.image_response_handler import save_forward_media
from lib.message_processing_handler import MessageProcessing
from lib.redis_handler import RedisCache
from lib.trigger_handler import process_vid_sub


class VideoResponse:
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

    def parse_video_response(self, response):
        # Video Response
        if not response.group_jid:
            # PM Video Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM Video Response" + Style.RESET_ALL)

            forward_queue = RedisCache(self.config).get_all_media_forward_queue(self.bot_id)
            for fu in forward_queue:
                if str(fu.decode("utf-8")) == response.from_jid:
                    data = json.loads(forward_queue[fu].decode("utf-8"))
                    time_check = time.time() - data["time"]
                    if time_check > 300:
                        RedisCache(self.config).rem_from_media_sub_queue(response.from_jid, self.bot_id)
                        return
                    time.sleep(1.5)
                    result = save_forward_media(self.config, response.from_jid, response.video_url, "video")
                    if result == 1:
                        members = RedisCache(self.config).get_single_group_data("json", "group_members", data["group_jid"])
                        display_name = "Unknown user"
                        for m in members:
                            if members[m]["jid"] == response.from_jid:
                                display_name = members[m]["display_name"]
                        self.client.send_chat_message(response.from_jid, "Forwarding your video. " + display_name)
                        video_file = self.config["paths"]["forward_img"] + response.from_jid + ".mp4"
                        thumbnail = self.config["paths"]["forward_img"] + response.from_jid + ".jpg"
                        dur = cv2.VideoCapture(video_file)
                        duration = dur.get(cv2.CAP_PROP_POS_MSEC)
                        self.client.send_chat_video(data["group_jid"], video_file, thumbnail, duration, False, False,
                                                    True, True, True)
                        self.client.send_chat_message(data["group_jid"], "Forwarded for: " + display_name)
                        RedisCache(self.config).rem_from_media_forward_queue(response.from_jid, self.bot_id)
                        if os.path.exists(self.config["paths"]["forward_img"] + response.from_jid + ".jpg"):
                            os.remove(self.config["paths"]["forward_img"] + response.from_jid + ".jpg")
                        if os.path.exists(self.config["paths"]["forward_img"] + response.from_jid + ".mp4"):
                            os.remove(self.config["paths"]["forward_img"] + response.from_jid + ".mp4")
                    else:
                        self.client.send_chat_message(response.from_jid, "Sending Failed. Try again.")

            remote_sessions = RedisCache(self.config).get_all_remote_sessions(self.bot_id)
            if response.from_jid.encode('utf-8') in remote_sessions:
                session_data = RedisCache(self.config).get_remote_session_data(response.from_jid, self.bot_id)
                # This is where we add value the remote group jid to chat_message
                response.remote_jid = response.from_jid  # this is correct I added second value to another to test
                response.group_jid = str(session_data["group_jid"]) + '@groups.kik.com'
                response.from_jid = session_data["user_ajid"]
                # Here we reset the timeout for this session because this is command is being sent to remote
                RedisCache(self.config).update_remote_session_data(response.from_jid, "last_activity", time.time(), self.bot_id)

                self.callback.on_video_received(response)

        else:
            # Group Video Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "Group Video Response" + Style.RESET_ALL)

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
            if "history" in group_data:
                RedisCache(self.config).set_single_history("video", response.from_jid, response.group_jid)
            else:
                if "group_members" in group_data:
                    RedisCache(self.config).add_all_history(group_data["group_members"], response.group_jid)
                    RedisCache(self.config).set_single_history("video", response.from_jid, response.group_jid)

            media_message_queue = RedisCache(self.config).get_all_media_message_queue(response.group_jid)
            for su in media_message_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(media_message_queue[su].decode('utf8'))
                    if sub_data["response"][:2] == "$i":
                        MessageProcessing(self).process_vid_media(response, sub_data["type"],
                                          sub_data["response"], response.image_url,
                                          response.from_jid, response.group_jid)

            sub_queue = RedisCache(self.config).get_all_media_sub_queue(response.group_jid)
            for su in sub_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(sub_queue[su].decode('utf8'))
                    if sub_data["response"][:2] == "$v":
                        process_vid_sub(self, response, sub_data["action"], sub_data["type"],
                                        sub_data["sub"],
                                        sub_data["response"], response.video_url,
                                        response.from_jid, response.group_jid)