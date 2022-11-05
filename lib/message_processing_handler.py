# Python 3 Core Libraries

# Python 3 Third Party Libraries

# Python 3 Project Libraries
# import json
# import os
import random
# import subprocess
import time
# import urllib.request
# import uuid
#
# import cv2
# import requests
#
# from lib.feature_status_handler import FeatureStatus
from lib.redis_handler import RedisCache
# from lib.remote_admin_handler import RemoteAdmin


bot_names = ["Luck 🍀", "Rage bot", "Adam 🍎", "Eve 🍏", "C​а​s​i​n​ο​ B​ο​t​", "Navi 🦋", "Unknown"]


def process_message(config, message_type, message, user_jid, group_jid, bot_id, days):
    group_data = RedisCache(config).get_all_group_data(group_jid)
    group_messages = group_data["group_messages"]
    group_hash = group_data["group_hash"]
    group_name = group_data["group_name"]

    if message_type == "join":  # Join message after user has been added to join queue
        user_info = RedisCache(config).get_single_join_queue(user_jid, bot_id)
        if "$u" in message or "{username}" in message:
            if user_info:
                message = message.replace("{username}", user_info["display_name"])
                message = message.replace("$u", user_info["display_name"])
            else:
                user_info = RedisCache(config).get_single_last_queue("joiner", group_jid)
                if user_info:
                    if user_info["alias_jid"] == user_jid:
                        message = message.replace("{username}", user_info["display_name"])
                        message = message.replace("$u", user_info["display_name"])

        if "$gh" in message:
            message = message.replace("$gh", group_hash)
        if "$gn" in message:
            if group_name is not None:
                message = message.replace("$gn", group_name)
        if "$d" in message or "{days}" in message:
            message = message.replace("$d", str(days))
            message = message.replace("{days}", str(days))
        return message
    elif message_type == "group":  # Group message user info comes from group data
        user_info = group_data["group_members"]
        if "$*" in message:
            message_list = message.split(" ")
            for l in message_list:
                if "$*" in l:
                    message = message.replace("$*", "🍀", 1)
        if "$ru" in message:
            message_list = message.split(" ")
            used_members = []
            for w in message_list:
                if "$ru" in w:
                    member_list = []
                    for m in user_info:
                        if user_info[m]["display_name"] in bot_names:
                            continue
                        elif user_info[m]["display_name"] in used_members:
                            continue
                        else:
                            member_list.append(user_info[m]["display_name"])
                            used_members.append(user_info[m]["display_name"])
                    member = random.choice(member_list)
                    message = message.replace("$ru", member, 1)
            if "$ru{" in message:
                random_users = message.count("$ru{")
                selected_users = []
                message_list = message.split(" ")
                count = 0
                for w in message_list:
                    if "$ru{" in w:
                        active = int(w.split("}")[0].replace("$ru{", "").replace("\n", ""))
                        active_time = active * 60
                        talker_list = []
                        talkers = RedisCache(config).get_all_talker_lurkers("talkers", group_jid)
                        for t in talkers:
                            active_in = int(time.time() - talkers[t])
                            if active_in < active_time:
                                if user_info[t]["display_name"] in bot_names:
                                    continue
                                elif user_info[t]["display_name"] in selected_users:
                                    continue
                                else:
                                    talker_list.append(t)

                        if len(talker_list) < random_users:
                            member = random.choice(talker_list)
                            selected_users.append(member)
                        else:
                            member = random.choice(selected_users)

                        message = message.replace("$ru{" + str(active) + "}", user_info[member]["display_name"], 1)
                    count += 1

            else:
                message_list = message.split(" ")
                for w in message_list:
                    if "$ru" in w:
                        member_list = []
                        for m in user_info:
                            if user_info[m]["display_name"] in bot_names:
                                continue
                            else:
                                member_list.append(user_info[m]["display_name"])
                        member = random.choice(member_list)
                        message = message.replace("$ru", member, 1)
        if "$rn" in message:
            if "$rn{" in message:
                message_list = message.split(" ")
                count = 0
                for w in message_list:
                    if "$rn{" in w:
                        max = int(w.split("}")[0].replace("$rn{", "").replace("\n", ""))
                        random_number = random.randint(1, max)
                        message = message.replace("$rn{" + str(max) + "}", str(random_number), 1)
                    count += 1

            else:
                message_list = message.split(" ")
                for w in message_list:
                    if "$rn" in w:
                        random_number = random.randint(1, 100)
                        message = message.replace("$rn", str(random_number), 1)
        if "$u" in message or "{username}" in message:
            if user_info is not None:
                message = message.replace("{username}", user_info[user_jid]["display_name"])
                message = message.replace("$u", user_info[user_jid]["display_name"])
        if "$gh" in message:
            if group_hash is not None:
                message = message.replace("$gh", group_hash)
        if "$gn" in message:
            if group_name is not None:
                message = message.replace("$gn", group_name)
        # if "$dh" in message:
        #     if group_settings and group_settings["redirect_group"] is not None:
        #         message = message.replace("$dh", group_settings["redirect_group"])
        #     else:
        #         message = message.replace("$dh", "#None")
        if "$d" in message or "{days}" in message:
            message = message.replace("{days}", str(days))
            message = message.replace("$d", str(days))
        return message
    elif message_type == "join_pre_queue":  # join message before user in join queue
        if "$u" in message or "{username}" in message:
            message = message.replace("{username}", user_jid)
            message = message.replace("$u", user_jid)
        if "$gh" in message:
            if group_hash is not None:
                message = message.replace("$gh", group_hash)
        if "$gn" in message:
            if group_name is not None:
                message = message.replace("$gn", group_name)
        # if "$dh" in message:
        #     if group_settings and group_settings["redirect_group"] is not None:
        #         message = message.replace("$dh", group_settings["redirect_group"])
        if "$d" in message or "{days}" in message:
            message = message.replace("{days}", str(days))
            message = message.replace("$d", str(days))
        return message


# def media_message_timeout(client, chat_message, peer_jid, group_jid):
#     RemoteAdmin(client).send_message(chat_message, "Send media you would like to set, you have 3 minutes.")
#     time.sleep(180)
#     sub_queue = RedisCache().get_all_media_message_queue(group_jid)
#     for su in sub_queue:
#         if str(su.decode("utf-8")) == peer_jid:
#             RedisCache().rem_from_media_message_queue(peer_jid, group_jid)
#
#
# def process_image_media(client, message, action, message_type, response, img_url, peer_jid, group_jid,
#                         bot_name):
#     sub_id = uuid.uuid4()
#     if "https://platform.kik.com/" in img_url:
#         if not os.path.exists(config.file_path["message_media"] + group_jid):
#             os.makedirs(config.file_path["message_media"] + group_jid)
#         time.sleep(1)
#         result = urllib.request.urlretrieve(img_url,
#                                             config.file_path["message_media"] + group_jid + "/" + str(sub_id) + ".jpg")
#         if result:
#             if len(response.split(" ")) > 1:
#                 text_media = response.split("$i ")[1] + " "
#             else:
#                 text_media = ''
#
#             # Set Group Language
#             group_settings = RedisCache().get_group_json("group_settings", message.group_jid)
#             if not group_settings:
#                 return
#             text = set_locale(group_settings["group_language"])
#
#             FeatureStatus(client).set_feature_message(message, message_type,
#                                                       f'{text_media}' + config.file_path["message_media"] + group_jid +
#                                                       "/" + str(sub_id) + ".jpg", bot_name, text)
#
#             RedisCache().rem_from_media_message_queue(peer_jid, group_jid)
#
#
# def process_gif_media(client, message, action, message_type, response, gif_data, peer_jid, group_jid,
#                       bot_name):
#     if gif_data:
#         gif_id = uuid.uuid4()
#         if len(response.split(" ")) > 1:
#             text_media = response.split("$g ")[1] + " "
#         else:
#             text_media = ''
#         if not os.path.exists(config.file_path["message_media"] + group_jid):
#             os.makedirs(config.file_path["message_media"] + group_jid)
#         with open(config.file_path["message_media"] + group_jid + "/" + str(gif_id) + ".json", "w+") as gif_save:
#             json.dump(gif_data, gif_save, indent=4)
#         gif_save.close()
#
#         # Set Group Language
#         group_settings = RedisCache().get_group_json("group_settings", message.group_jid)
#         if not group_settings:
#             return
#         text = set_locale(group_settings["group_language"])
#         FeatureStatus(client).set_feature_message(message, message_type,
#                                                   f'{text_media}' + config.file_path["message_media"] + group_jid +
#                                                   "/" + str(gif_id) + ".json", bot_name, text)
#         RedisCache().rem_from_media_message_queue(peer_jid, group_jid)
#
#
# def process_vid_media(client, message, action, message_type, response, vid_url, peer_jid, group_jid,
#                       bot_name):
#     vid_id = uuid.uuid4()
#     if "https://platform.kik.com/" in vid_url:
#         if not os.path.exists(config.file_path["message_media"] + group_jid):
#             os.makedirs(config.file_path["message_media"] + group_jid)
#         time.sleep(1)
#         vid = requests.get(vid_url, stream=True)
#         if vid.status_code == 200:
#             with open(config.file_path["message_media"] + group_jid + "/" + str(vid_id) + ".mp4", 'wb') as f:
#                 for chunk in vid.iter_content(chunk_size=1024 * 1024):
#                     if chunk:
#                         f.write(chunk)
#                 f.close()
#             thumbnail = config.file_path["message_media"] + group_jid + "/" + str(vid_id) + ".jpg"
#             video = config.file_path["message_media"] + group_jid + "/" + str(vid_id) + ".mp4"
#             command = "ffmpeg -i {} -ss 00:00:00.000 -vframes 1 {}".format(video, thumbnail)
#             if len(response.split(" ")) > 1:
#                 text_media = response.split("$v ")[1] + " "
#             else:
#                 text_media = ''
#             result = subprocess.run(
#                 # Command as a list, to avoid shell=True
#                 command.split(),
#                 # Expect textual output, not bytes; let Python .decode() on the fly
#                 text=True,
#                 # Shorthand for stdout=PIPE stderr=PIPE etc etc
#                 capture_output=True,
#                 # Raise an exception if ping fails (maybe try/except it separately?)
#                 check=True)
#
#             # Set Group Language
#             group_settings = RedisCache().get_group_json("group_settings", message.group_jid)
#             if not group_settings:
#                 return
#             text = set_locale(group_settings["group_language"])
#
#             FeatureStatus(client).set_feature_message(message, message_type,
#                                                       f'{text_media}' + config.file_path["message_media"] + group_jid +
#                                                       "/" + str(vid_id) + ".mp4", bot_name, text)
#
#             RedisCache().rem_from_media_message_queue(peer_jid, group_jid)
#
#
# def process_message_media(client, message_type, message_response, peer_jid, group_jid):
#     if message_response[-3:] == "mp4":
#         if message_response[:1] == "[":
#             text_response = message_response.split("] ")[0].replace("[", "").replace("]", "")
#             vid_response = message_response.split("] ")[1]
#             if message_type == "exit_message":
#                 text_message = process_message("group", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             elif message_type == "welcome_message_pre":
#                 text_message = process_message("join_pre_queue", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             else:
#                 text_message = process_message("join", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             video = vid_response
#             thumbnail = vid_response.replace("mp4", "jpg")
#             dur = cv2.VideoCapture(video)
#             duration = dur.get(cv2.CAP_PROP_POS_MSEC)
#             client.send_chat_video(group_jid, video, thumbnail, duration)
#             time.sleep(1.5)
#             client.send_chat_message(group_jid, text_message)
#         else:
#             video = message_response
#             thumbnail = message_response.replace("mp4", "jpg")
#             dur = cv2.VideoCapture(video)
#             duration = dur.get(cv2.CAP_PROP_POS_MSEC)
#             client.send_chat_video(group_jid, video, thumbnail, duration)
#         return
#     elif message_response[-3:] == "png" or message_response[-3:] == "jpg":
#         if message_response[:1] == "[":
#             text_response = message_response.split("] ")[0].replace("[", "").replace("]", "")
#             image_response = message_response.split("] ")[1]
#             if message_type == "exit_message":
#                 text_message = process_message("group", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             elif message_type == "welcome_message_pre":
#                 text_message = process_message("join_pre_queue", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             else:
#                 text_message = process_message("join", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             client.send_chat_image(group_jid, image_response)
#             time.sleep(1.5)
#             client.send_chat_message(group_jid, text_message)
#         else:
#             client.send_chat_image(group_jid, message_response)
#         return
#     elif message_response[-4:] == "json":
#         if message_response[:1] == "[":
#             text_response = message_response.split("] ")[0].replace("[", "").replace("]", "")
#             image_response = message_response.split("] ")[1]
#             if message_type == "exit_message":
#                 text_message = process_message("group", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             elif message_type == "welcome_message_pre":
#                 text_message = process_message("join_pre_queue", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             else:
#                 text_message = process_message("join", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             client.send_gif_image_sub(group_jid, image_response)
#             time.sleep(1.5)
#             client.send_chat_message(group_jid, text_message)
#         else:
#             client.send_gif_image_sub(group_jid, message_response)
#         return
#     elif message_response[:3] == "$gs":
#         if "[" in message_response[4:]:
#             text_response = message_response[4:].split("] ")[0].replace("[", "").replace("]", "")
#             search_term = message_response[4:].split("] ")[1]
#             if message_type == "exit_message":
#                 text_message = process_message("group", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             elif message_type == "welcome_message_pre":
#                 text_message = process_message("join_pre_queue", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             else:
#                 text_message = process_message("join", text_response,
#                                                peer_jid,
#                                                group_jid,
#                                                "0", "0")
#             client.send_gif_image(group_jid, search_term)
#             time.sleep(1.5)
#             client.send_chat_message(group_jid, text_message)
#             return
#         else:
#             search_term = message_response[4:]
#             client.send_gif_image(group_jid, search_term)
#             return
#     elif message_response[:2] == "$l":
#         title = message_response.split("$l ")[1].split("\n")[0]
#         text = message_response.split("$l ")[1].split("\n")[1]
#         link = message_response.split("$l ")[1].split("\n")[2]
#         app = link.lower().split("https://")[1].split("/")[0]
#         client.send_link(group_jid, link, title, text, app)
#         return
#     else:
#         if message_type == "exit_message":
#             text_message = process_message("group", message_response,
#                                            peer_jid,
#                                            group_jid,
#                                            "0", "0")
#         elif message_type == "welcome_message_pre":
#             text_message = process_message("join_pre_queue", message_response,
#                                            peer_jid,
#                                            group_jid,
#                                            "0", "0")
#         else:
#             text_message = process_message("join", message_response,
#                                            peer_jid,
#                                            group_jid,
#                                            "0", "0")
#         client.send_chat_message(group_jid, text_message)
#         return
