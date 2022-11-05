import json
import time

from colorama import Fore, Style

from lib.redis_handler import RedisCache
from lib.trigger_handler import process_vid_sub


class VideoResponse:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def parse_video_response(self, response):
        # Video Response
        if not response.group_jid:
            # PM Video Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM Video Response" + Style.RESET_ALL)

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

            sub_queue = RedisCache(self.config).get_all_media_sub_queue(response.group_jid)
            for su in sub_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(sub_queue[su].decode('utf8'))
                    if sub_data["response"][:2] == "$v":
                        process_vid_sub(self, response, sub_data["action"], sub_data["type"],
                                        sub_data["sub"],
                                        sub_data["response"], response.video_url,
                                        response.from_jid, response.group_jid)