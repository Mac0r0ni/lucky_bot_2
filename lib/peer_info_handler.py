import random
import time

from colorama import Fore, Style

from lib.group_init_update_handler import GroupInitUpdate
from lib.redis_handler import RedisCache
from lib.user_process_handler import UserProcess


class PeerInfo:
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

    def peer_info_parser(self, response):
        grab_queue = RedisCache(self.config).get_all_grab_queue(self.bot_id)
        if self.config["general"]["debug"] == 1:
            users = '\n'.join([str(member) for member in response.users])
            print(self.info + f'Peer info: {users}')

        if len(response.users) > 1:
            res_dict = {}
            for i in response.users:
                if i.pic is not None:
                    res_dict[i.jid] = {"display_name": i.display_name, "pfp": i.pic + "/orig.jpg"}
                else:
                    res_dict[i.jid] = {"display_name": i.display_name,
                                       "pfp": "default.jpg"}

            group_queue = RedisCache(self.config).get_group_queue(self.bot_id)
            for gr in group_queue:
                g_data = RedisCache(self.config).get_single_group_queue(gr, self.bot_id)
                if g_data["info_id_1"] == response.message_id and g_data["info_id_2"] == "None":

                    owner_dict, admins_dict, members_dict = process_peer_data(res_dict, g_data)

                    processed_members = process_group_users(members_dict, gr, self.bot_id, self.config)

                    GroupInitUpdate(self).update_add_database(g_data["scope"], g_data["group_hash"],
                                                                     g_data["group_name"],
                                                                     g_data["group_status"],
                                                                     owner_dict, admins_dict, processed_members, gr.decode('utf-8'), self.bot_id)
                elif g_data["info_id_1"] == response.message_id and g_data["info_id_2"] != "None":
                    # No Database update
                    owner_dict, admins_dict, members_dict = process_peer_data(res_dict, g_data)

                    RedisCache(self.config).update_group_queue_json("owner_resp", owner_dict, gr, self.bot_id)
                    RedisCache(self.config).update_group_queue_json("admins_resp", admins_dict, gr, self.bot_id)
                    RedisCache(self.config).update_group_queue_json("members_resp", members_dict, gr, self.bot_id)
                    RedisCache(self.config).update_group_queue_json("info_id_1", "None", gr, self.bot_id)

                elif g_data["info_id_2"] == response.message_id and g_data["info_id_1"] == "None":
                    # Database update
                    owner_dict, admins_dict, members_dict = process_peer_data(res_dict, g_data)

                    processed_members = process_group_users(members_dict, gr, self.bot_id, self.config)

                    GroupInitUpdate(self).update_add_database(g_data["scope"], g_data["group_hash"],
                                                                     g_data["group_name"],
                                                                     g_data["group_status"],
                                                                     owner_dict, admins_dict, processed_members,
                                                                     gr.decode('utf-8'), self.bot_id)

                elif g_data["info_id_2"] == response.message_id and g_data["info_id_1"] != "None":
                    # No Database update
                    time.sleep(1)
                    self.callback.on_peer_info_received(response)

        elif len(response.users) == 1 and response.users[0]:
            # Single users peer data
            if response.users[0].pic is not None:
                response_data = {"username": response.users[0].username, "display_name": response.users[0].display_name,
                                 "jid": response.users[0].jid, "pfp": response.users[0].pic + "/orig.jpg"}
            else:
                response_data = {"username": response.users[0].username, "display_name": response.users[0].display_name,
                                 "jid": response.users[0].jid,
                                 "pfp": "default.jpg"}

            if grab_queue:
                if response.users[0].display_name.encode("utf-8") in grab_queue:
                    peer_data = RedisCache(self.config).get_single_grab_queue(response.users[0].display_name, self.bot_id)
                    self.client.send_chat_message(peer_data["group_jid"],
                                                  response.users[0].display_name + " is @" + response.users[0].username)
                    RedisCache(self.config).remove_from_grab_queue(response.users[0].display_name, self.bot_id)

            RedisCache(self.config).add_peer_response_data(response_data, self.bot_id)

    def xiphias_info_parser(self, response):
        if self.config["general"]["debug"] == 1:
            users = '\n'.join([str(member) for member in response.users])
            print(self.info + f'Peer info: {users}')

        if len(response.users) < 1:
            return
        elif len(response.users) == 1:
            if "alias_jid" in response.users[0].__dict__:
                join_queue = RedisCache(self.config).get_all_join_queue(self.bot_id)
                if join_queue:
                    if response.users[0].alias_jid.encode('utf-8') in join_queue:
                        time.sleep(2)
                        join_data = RedisCache(self.config).get_single_join_queue(response.users[0].alias_jid, self.bot_id)
                        peer_data = RedisCache(self.config).get_peer_data(response.users[0].display_name, self.bot_id)
                        if join_data:
                            # User is in join queue waiting to be processed. Send user data to join Class to process
                            UserProcess(self).process_join_user(peer_data, response.users[0], response.users[0].alias_jid,
                                              join_data)
            else:
                join_queue = RedisCache(self.config).get_all_join_queue(self.bot_id)
                if join_queue:
                    if response.users[0].jid.encode('utf-8') in join_queue:
                        time.sleep(2)
                        join_data = RedisCache(self.config).get_single_join_queue(response.users[0].jid, self.bot_id)
                        peer_data = RedisCache(self.config).get_peer_data(response.users[0].display_name, self.bot_id)
                        if join_data:
                            UserProcess(self).process_join_user(peer_data, response.users[0], response.users[0].jid, join_data)


def process_peer_data(res_dict, group_data):
    owner_dict = {}
    admins_dict = {}
    members_dict = {}

    if group_data["owner_resp"]:
        owner_dict.update(group_data["owner_resp"])
    if group_data["admins_resp"]:
        admins_dict.update(group_data["admins_resp"])
    if group_data["members_resp"]:
        members_dict.update(group_data["members_resp"])

    for m in res_dict:
        if m in group_data["owner"]:
            owner_dict.update({m: res_dict[m]["display_name"]})
        if m in group_data["admins"]:
            admins_dict.update({m: res_dict[m]["display_name"]})
        if m in group_data["members"]:
            members_dict.update({m: {"display_name": res_dict[m]["display_name"], "pfp": res_dict[m]["pfp"]}})
    return owner_dict, admins_dict, members_dict


def process_group_users(members_dict, gr, bot_id, config_data):
    processed_members = {}
    numbers_all = list(range(1, 107))
    last_queue = RedisCache(config_data).get_single_last_queue("joiner", gr.decode("utf-8"))
    current_members = RedisCache(config_data).get_single_group_data("json", "group_members", gr.decode('utf-8'))
    if current_members:
        for i in current_members:
            if i in members_dict:
                # remove uid from list if in use
                uid = current_members[i]["uid"]
                if uid:
                    if uid in numbers_all:
                        numbers_all.remove(uid)

    for m in members_dict:
        if current_members:
            if m in current_members:
                peer_data = RedisCache(config_data).get_peer_data(members_dict[m]["display_name"], bot_id)
                if peer_data:
                    if last_queue:
                        if last_queue["alias_jid"] == m:
                            RedisCache(config_data).update_last_queue_user("joiner", "user_jid", peer_data["jid"],
                                                                gr.decode("utf-8"))
                    processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                                  "pfp": members_dict[m]["pfp"],
                                                  "username": peer_data["username"],
                                                  "jid": peer_data["jid"],
                                                  "nickname": current_members[m]["nickname"],
                                                  "uid": current_members[m]["uid"],
                                                  "cap_whitelist": current_members[m]["cap_whitelist"],
                                                  "history": current_members[m]["history"],
                                                  "join_time": current_members[m]["join_time"],
                                                  "xp": current_members[m]["xp"],
                                                  "level": current_members[m]["level"],
                                                  "currency": current_members[m]["currency"]}})

                else:
                    processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                                  "pfp": members_dict[m]["pfp"],
                                                  "username": current_members[m]["username"],
                                                  "jid": current_members[m]["jid"],
                                                  "nickname": current_members[m]["nickname"],
                                                  "uid": current_members[m]["uid"],
                                                  "cap_whitelist": current_members[m]["cap_whitelist"],
                                                  "history": current_members[m]["history"],
                                                  "join_time": current_members[m]["join_time"],
                                                  "xp": current_members[m]["xp"],
                                                  "level": current_members[m]["level"],
                                                  "currency": current_members[m]["currency"]}})
            else:
                uid = random.choice(numbers_all)
                numbers_all.remove(uid)
                peer_data = RedisCache(config_data).get_peer_data(members_dict[m]["display_name"], bot_id)
                if peer_data:
                    if last_queue:
                        if last_queue["alias_jid"] == m:
                            RedisCache(config_data).update_last_queue_user("joiner", "user_jid", peer_data["jid"],
                                                                gr.decode("utf-8"))
                    processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                                  "pfp": members_dict[m]["pfp"],
                                                  "username": peer_data["username"],
                                                  "jid": peer_data["jid"],
                                                  "nickname": members_dict[m]["display_name"],
                                                  "uid": uid,
                                                  "cap_whitelist": 0,
                                                  "history": {"message": 0, "image": 0, "video": 0, "gif": 0},
                                                  "join_time": time.time(),
                                                  "xp": 0,
                                                  "level": 0,
                                                  "currency": 100}})

                else:
                    processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                                  "pfp": members_dict[m]["pfp"],
                                                  "username": "Unknown",
                                                  "jid": "Unknown",
                                                  "nickname": members_dict[m]["display_name"],
                                                  "uid": uid,
                                                  "cap_whitelist": 0,
                                                  "history": {"message": 0, "image": 0, "video": 0, "gif": 0},
                                                  "join_time": time.time(),
                                                  "xp": 0,
                                                  "level": 0,
                                                  "currency": 100}})
        else:
            uid = random.choice(numbers_all)
            numbers_all.remove(uid)
            peer_data = RedisCache(config_data).get_peer_data(members_dict[m]["display_name"], bot_id)
            if peer_data:
                if last_queue:
                    if last_queue["alias_jid"] == m:
                        RedisCache(config_data).update_last_queue_user("joiner", "user_jid", peer_data["jid"],
                                                                       gr.decode("utf-8"))
                processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                              "pfp": members_dict[m]["pfp"],
                                              "username": peer_data["username"],
                                              "jid": peer_data["jid"],
                                              "nickname": members_dict[m]["display_name"],
                                              "uid": uid,
                                              "cap_whitelist": 0,
                                              "history": {"message": 0, "image": 0, "video": 0, "gif": 0},
                                              "join_time": time.time(),
                                              "xp": 0,
                                              "level": 0,
                                              "currency": 100}})

            else:
                processed_members.update({m: {"display_name": members_dict[m]["display_name"],
                                              "pfp": members_dict[m]["pfp"],
                                              "username": "Unknown",
                                              "jid": "Unknown",
                                              "nickname": members_dict[m]["display_name"],
                                              "uid": uid,
                                              "cap_whitelist": 0,
                                              "history": {"message": 0, "image": 0, "video": 0, "gif": 0},
                                              "join_time": time.time(),
                                              "xp": 0,
                                              "level": 0,
                                              "currency": 100}})
    return processed_members
