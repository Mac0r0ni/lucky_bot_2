import json
import os
import shutil
import subprocess
import time
import cv2
import numpy as np
import requests

from colorama import Fore, Style

from lib.message_processing_handler import MessageProcessing
from lib.redis_handler import RedisCache
from lib.trigger_handler import process_image_sub


class ImageResponse:
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

    def parse_image_response(self, response):
        # Image Response
        if not response.group_jid:
            # PM Image Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM Image Response" + Style.RESET_ALL)

            forward_queue = RedisCache(self.config).get_all_media_forward_queue(self.bot_id)
            for fu in forward_queue:
                if str(fu.decode("utf-8")) == response.from_jid:
                    data = json.loads(forward_queue[fu].decode("utf-8"))
                    time_check = time.time() - data["time"]
                    if time_check > 300:
                        RedisCache(self.config).rem_from_media_forward_queue(response.from_jid, self.bot_id)
                        return
                    time.sleep(1.5)
                    result = save_forward_media(self.config, response.from_jid, response.image_url, "image")
                    if result == 1:
                        members = RedisCache(self.config).get_single_group_data("json", "group_members", data["group_jid"])
                        display_name = "Unknown user"
                        for m in members:
                            if members[m]["jid"] == response.from_jid:
                                display_name = members[m]["display_name"]
                        self.client.send_chat_message(response.from_jid, "Forwarding your image. " + display_name)
                        self.client.send_chat_image(data["group_jid"],
                                                    self.config["paths"]["forward_img"] + response.from_jid + ".jpg")
                        self.client.send_chat_message(data["group_jid"], "Forwarded for: " + display_name)
                        RedisCache(self.config).rem_from_media_forward_queue(response.from_jid, self.bot_id)
                        if os.path.exists(self.config["paths"]["forward_img"] + response.from_jid + ".jpg"):
                            os.remove(self.config["paths"]["forward_img"] + response.from_jid + ".jpg")
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
                RedisCache(self.config).update_remote_session_data(response.from_jid, "last_activity", time.time(),
                                                                   self.bot_id)

                self.callback.on_image_received(response)

        else:
            # Group Image Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "Group Image Response" + Style.RESET_ALL)
            if response.group_jid == "1100257133458_g@groups.kik.com":
                print(self.info + "Group Image Response" + Style.RESET_ALL)
            group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
            if not group_data:
                print(self.critical + "No Group Data for Image Response")
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
                RedisCache(self.config).set_single_history("image", response.from_jid, response.group_jid)
            else:
                if "group_members" in group_data:
                    RedisCache(self.config).add_all_history(group_data["group_members"], response.group_jid)
                    RedisCache(self.config).set_single_history("image", response.from_jid, response.group_jid)

            media_message_queue = RedisCache(self.config).get_all_media_message_queue(response.group_jid)
            for su in media_message_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(media_message_queue[su].decode('utf8'))
                    if sub_data["response"][:2] == "$i":
                        MessageProcessing(self).process_image_media(response, sub_data["type"],
                                                                    sub_data["response"], response.image_url,
                                                                    response.from_jid, response.group_jid)

            sub_queue = RedisCache(self.config).get_all_media_sub_queue(response.group_jid)
            for su in sub_queue:
                if str(su.decode("utf-8")) == response.from_jid:
                    sub_data = json.loads(sub_queue[su].decode('utf8'))
                    if sub_data["response"][:2] == "$i":
                        print(self.warning + "Found in media sub queue, processing")
                        process_image_sub(self, response, sub_data["action"], sub_data["type"],
                                          sub_data["sub"],
                                          sub_data["response"], response.image_url,
                                          response.from_jid, response.group_jid)


def check_pfp(config, peer_jid):
    file_names = ["default.jpg"]
    match = 0
    for f in file_names:
        img_rgb = cv2.imread(config["paths"]["user_img"] + peer_jid + ".jpg")
        template = cv2.imread(config["paths"]["user_img"] + f)
        w, h = template.shape[:-1]

        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        threshold = .8
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
            match += 1
    return match


def media_forward_timeout(config, client, peer_jid, group_jid, bot_id):
    client.send_chat_message(group_jid, "Send image or video to my PM @lucky_bot_" + str(bot_id) + "\n You have 2 minutes.")
    time.sleep(120)
    sub_queue = RedisCache(config).get_all_media_forward_queue(bot_id)
    for su in sub_queue:
        if str(su.decode("utf-8")) == peer_jid:
            RedisCache(config).rem_from_media_forward_queue(peer_jid, bot_id)


def save_forward_media(config, peer_jid, media_url, media_type):
    if media_type == "image":
        img = requests.get(media_url, stream=True)
        if img.status_code == 200:
            with open(config["paths"]["forward_img"] + peer_jid + ".jpg", 'wb') as f:
                img.raw.decode_content = True
                shutil.copyfileobj(img.raw, f)
                f.close()
            return 1
        else:
            return 2
    elif media_type == "video":
        vid = requests.get(media_url, stream=True)
        if vid.status_code == 200:
            with open(config["paths"]["forward_img"] + peer_jid + ".mp4", 'wb') as f:
                for chunk in vid.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                f.close()
            thumbnail = config["paths"]["forward_img"] + peer_jid + ".jpg"
            video = config["paths"]["forward_img"] + peer_jid + ".mp4"
            command = "ffmpeg -i {} -ss 00:00:00.000 -vframes 1 {}".format(video, thumbnail)
            result = subprocess.run(
                # Command as a list, to avoid shell=True
                command.split(),
                # Expect textual output, not bytes; let Python .decode() on the fly
                text=True,
                # Shorthand for stdout=PIPE stderr=PIPE etc etc
                capture_output=True,
                # Raise an exception if ping fails (maybe try/except it separately?)
                check=True)
            return 1
        else:
            return 2
    else:
        return 2
