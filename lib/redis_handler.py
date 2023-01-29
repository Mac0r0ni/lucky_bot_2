# Python 3 Core Libraries
import time
import json

# Python 3 Third Party Libraries
import redis
from colorama import Fore, Style


# Python 3 Project Libraries


class RedisCache:
    def __init__(self, config_data):
        self.redis_host = config_data["redis"]["hostname"]
        self.redis_port = config_data["redis"]["port"]
        self.redis_password = config_data["redis"]["password"]
        self.config = config_data
        self.debug = f'[' + Style.BRIGHT + Fore.MAGENTA + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.GREEN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

        if config_data["redis"]["password"]:
            self.r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password)
        else:
            self.r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port)

    # ------------------------------------
    #  Redis Cache - Cache Creation for Groups
    # ------------------------------------

    # uses pipe to add all data to cache
    def add_to_cache(self, data, column_list):
        # opens the pipe line
        with self.r.pipeline() as pipe:
            # iterate out data
            for k in data:
                i = 1
                # iterate our column list
                for c in column_list:
                    # set the column/value in cache
                    pipe.hset(k[0], c, str(k[i]))
                    i += 1
            # Finalize the pipe by executing
            pipe.execute()

    def get_single_group_data(self, type, key, group_jid):
        group_jid = group_jid.split('@')[0]
        data = self.r.hget(str(group_jid), key)
        if data:
            if type == "json" or type == "list":
                return json.loads(data)
            elif type == "str":
                return str(data.decode("utf-8"))
            elif type == "int":
                return int(data.decode("utf-8"))
            else:
                return data.decode()
        else:
            return ""

    def get_all_group_data(self, group_jid):
        group_data = {}
        group_jid = group_jid.split('@')[0]
        data = self.r.hgetall(str(group_jid))
        if data:
            for key, value in data.items():
                if value.decode().startswith("{") or value.decode().startswith("["):
                    try:
                        group_data[key.decode("utf-8")] = json.loads(value.decode("utf8"))
                    except Exception as e:
                        print(repr(e))
                        return False

                elif value.decode().isnumeric():
                    group_data[key.decode("utf-8")] = int(value.decode("utf-8"))
                else:
                    group_data[key.decode("utf-8")] = value.decode("utf-8")

            return group_data
        else:
            return False

    def update_group_data(self, key, value, group_jid):
        group_jid = group_jid.split('@')[0]
        data = self.r.hgetall(str(group_jid))
        if data:
            if type(value) is list or type(value) is dict:
                self.r.hset(str(group_jid), key, json.dumps(value))
                return True
            else:
                self.r.hset(str(group_jid), key, value)
                return True
        else:
            return False

    def remove_group_from_cache(self, group_jid):
        group_jid = group_jid.split('@')[0]
        self.r.delete(group_jid)

    # ------------------------------------
    #  Redis Cache - Talkers/Lurkers
    # ------------------------------------

    def add_single_talker_lurker(self, activity, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], activity)
        if data:
            data_json = json.loads(data)
            data_json[user_jid] = 0
            self.r.hset(group_jid.split('@')[0], activity, json.dumps(data_json))
        else:
            members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
            if members:
                RedisCache(self.config).add_all_talker_lurker("talkers", members, group_jid)
                RedisCache(self.config).add_all_talker_lurker("lurkers", members, group_jid)

    def remove_single_talker_lurker(self, activity, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], activity)
        if data:
            data_json = json.loads(data)
            if user_jid in data_json:
                del data_json[user_jid]
                self.r.hset(group_jid.split('@')[0], activity, json.dumps(data_json))

    def set_single_talker_lurker(self, activity, time, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], activity)
        if data:
            data_json = json.loads(data)
            data_json[user_jid] = time
            self.r.hset(group_jid.split('@')[0], activity, json.dumps(data_json))
        else:
            members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
            if members:
                RedisCache(self.config).add_all_talker_lurker("talkers", members, group_jid)
                RedisCache(self.config).add_all_talker_lurker("lurkers", members, group_jid)

    def get_all_talker_lurkers(self, activity, group_jid):
        data = self.r.hget(group_jid.split('@')[0], activity)
        if data:
            data_json = json.loads(data)
            return data_json
        else:
            return False

    def add_all_talker_lurker(self, activity, member_list, group_jid):
        data = {}
        for m in member_list:
            data[m] = 0
        self.r.hset(group_jid.split('@')[0], activity, json.dumps(data))

    def remove_all_talker_lurkers(self, activity, group_jid):
        self.r.delete(group_jid.split('@')[0], activity)

    def reset_all_talker_lurkers(self, activity, group_jid):
        self.r.delete(group_jid.split('@')[0], activity)
        members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
        if members:
            RedisCache(self.config).add_all_talker_lurker(activity, members, group_jid)

    def add_timer_cache(self, timer_jid, group_jid):
        peer_data = {"stop": False}
        self.r.hset(group_jid.split('@')[0] + "_timer_cache", timer_jid, json.dumps(peer_data))

    def get_all_timer_cache(self, group_jid):
        data = self.r.hgetall(group_jid.split('@')[0] + "_timer_cache")
        if data:
            return data
        else:
            return False

    # ------------------------------------
    #  Redis Cache - Timer Data
    # ------------------------------------

    def update_timer_cache(self, timer_jid, group_jid):
        peer_data = {"stop": True}
        self.r.hset(group_jid.split('@')[0] + "_timer_cache", timer_jid, json.dumps(peer_data))

    def get_timer_cache(self, peer_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0] + "_timer_cache", peer_jid)
        if data:
            return json.loads(data)
        else:
            return False

    def rem_from_timer_cache(self, peer_jid, group_jid):
        self.r.hdel(group_jid.split('@')[0] + "_timer_cache", peer_jid)

    # -----------------------------------------
    #  Redis Cache - Group Data Cache
    # -----------------------------------------

    def add_to_group_queue_cache(self, scope, info_id_1, info_id_2, group_hash, group_name, bot_id, status, owner,
                                 admins, members, group_jid):
        group_data = {"scope": scope, "info_id_1": info_id_1, "info_id_2": info_id_2, "group_status": status,
                      "group_name": group_name, "group_hash": group_hash, "owner": {},
                      "admins": {},
                      "members": {}, "owner_resp": {}, "admins_resp": {}, "members_resp": {}}

        for m in members:
            group_data["members"][m.jid] = {}
            group_data["members"][m.jid]["display_name"] = "Unknown"
        for a in admins:
            group_data["admins"][a] = {}
            group_data["admins"][a]["display_name"] = "Unknown"
        for o in owner:
            group_data["owner"][o] = {}
            group_data["owner"][o]["display_name"] = "Unknown"

        self.r.hset(str(bot_id) + "_group_queue", group_jid, json.dumps(group_data))

    def get_group_queue(self, bot_id):
        group_queue = self.r.hgetall(str(bot_id) + "_group_queue")
        if group_queue is not None:
            return group_queue
        else:
            return False

    def update_group_queue_json(self, key, value, group_jid, bot_id):
        data = self.r.hget(str(bot_id) + "_group_queue", group_jid)
        if data:
            group_data = json.loads(data)
            group_data[key] = value
            self.r.hset(str(bot_id) + "_group_queue", group_jid, json.dumps(group_data))
        else:
            print("No Data")

    def get_single_group_queue(self, group_jid, bot_id):
        group = self.r.hget(str(bot_id) + "_group_queue", group_jid)
        if group is not None:
            return json.loads(group)
        else:
            return False

    def remove_from_group_queue(self, group_jid, bot_id):
        self.r.hdel(str(bot_id) + "_group_queue", group_jid)

    def remove_all_from_group_queue(self, bot_id):
        self.r.delete(str(bot_id) + "_group_queue")

    # -----------------------------------------
    #  Redis Cache - Bot Data From Cache
    # -----------------------------------------

    def get_bot_config_data(self, type, key, bot_id):
        data = self.r.hget(str(bot_id), key)
        if data:
            if type == "json" or type == "list":
                return json.loads(data)
            elif type == "str":
                return str(data.decode())
            elif type == "int":
                return int(data.decode())
            else:
                return data.decode()
        else:
            return ""

    def get_all_bot_config_data(self, bot_id):
        bot_config_data = {}
        data = self.r.hgetall(str(bot_id))
        if data:
            for key, value in data.items():
                if value.decode().startswith("{") or value.decode().startswith("["):
                    bot_config_data[key.decode("utf-8")] = json.loads(value)
                elif value.decode().isnumeric():
                    bot_config_data[key.decode("utf-8")] = int(value.decode())
                else:
                    bot_config_data[key.decode("utf-8")] = value.decode()

            return bot_config_data
        else:
            return ""

    # ------------------------------------
    #  Redis Cache - Peer Info Queue
    # ------------------------------------

    def add_peer_response_data(self, response_data, bot_id):
        self.r.hset(str(bot_id) + "_peer_data", response_data["display_name"], json.dumps(response_data))

    def get_all_peer_data(self, bot_id):
        data = self.r.hget(str(bot_id) + "_peer_data", bot_id)
        if data:
            return data
        else:
            return False

    def get_peer_data(self, display_name, bot_id):
        data = self.r.hget(str(bot_id) + "_peer_data", display_name)
        if data:
            return json.loads(data)
        else:
            return False

    def remove_peer_data(self, display_name, bot_id):
        self.r.hdel(str(bot_id) + "_peer_data", display_name)

    def remove_all_from_peer_data(self, bot_id):
        self.r.delete(str(bot_id) + "_peer_data")

    # ------------------------------------
    #  Redis Cache - last join/remove/ban cache
    # ------------------------------------

    def get_all_last_queue(self, last_type, group_jid):
        join_queue = self.r.hgetall(group_jid + f'_last_{last_type}_queue')
        if join_queue:
            return join_queue
        else:
            return False

    def get_single_last_queue(self, last_type, group_jid):
        user_data = self.r.hget(group_jid + f'_last_{last_type}_queue', "last")
        if user_data is not None:
            return json.loads(user_data)
        else:
            return False

    def add_to_last_queue(self, last_type, peer_data, group_jid):
        self.r.hset(group_jid + f'_last_{last_type}_queue', "last", json.dumps(peer_data))

    def remove_from_last_queue(self, last_type, group_jid):
        self.r.hdel(group_jid + f'_last_{last_type}_queue', "last")

    def remove_all_from_last_queue(self, last_type, group_jid):
        self.r.delete(group_jid + f'_last_{last_type}_queue')

    def update_last_queue_user(self, last_type, key, value, group_jid):
        user_data = self.get_single_last_queue(last_type, group_jid)
        user_data[key] = value

    # ------------------------------------
    #  Redis Cache - User Join Queue
    # ------------------------------------

    def get_all_join_queue(self, bot_id):
        join_queue = self.r.hgetall(str(bot_id) + "_join_queue")
        if join_queue:
            return join_queue
        else:
            return False

    def get_single_join_queue(self, peer_jid, bot_id):
        user_data = self.r.hget(str(bot_id) + "_join_queue", peer_jid)
        if user_data is not None:
            return json.loads(user_data)
        else:
            return False

    def add_to_join_queue(self, peer_jid, peer_data, bot_id):
        self.r.hset(str(bot_id) + "_join_queue", peer_jid, json.dumps(peer_data))

    def remove_from_join_queue(self, peer_jid, bot_id):
        self.r.hdel(str(bot_id) + "_join_queue", peer_jid)

    def remove_all_from_join_queue(self, bot_id):
        self.r.delete(str(bot_id) + "_join_queue")

    # ------------------------------------
    #  Redis Cache - Name Grab Peer Queue
    # ------------------------------------

    def update_join_queue_user(self, key, value, peer_jid, bot_id):
        user_data = self.get_single_join_queue(peer_jid, bot_id)
        user_data[key] = value
        self.r.hset(str(bot_id) + "_join_queue", peer_jid, json.dumps(user_data))

    def add_to_grab_queue(self, peer_display_name, group_jid, bot_id):
        queue_data = {"group_jid": group_jid}
        self.r.hset(str(bot_id) + "_grab_queue", peer_display_name, json.dumps(queue_data))

    def get_all_grab_queue(self, bot_id):
        group_queue = self.r.hgetall(str(bot_id) + "_grab_queue")
        if group_queue is not None:
            return group_queue
        else:
            return False

    def get_single_grab_queue(self, peer_display_name, bot_id):
        data = self.r.hget(str(bot_id) + "_grab_queue", peer_display_name)
        if data is not None:
            return json.loads(data)
        else:
            return False

    def remove_from_grab_queue(self, peer_display_name, bot_id):
        self.r.hdel(str(bot_id) + "_grab_queue", peer_display_name)

    def remove_all_from_grab_queue(self, bot_id):
        self.r.delete(str(bot_id) + "_grab_queue")

    # ------------------------------------
    #  Redis Cache - Remote Session Cache
    # ------------------------------------

    def get_all_remote_sessions(self, bot_id):
        sessions = self.r.hgetall(str(bot_id) + "_remote_session_data")
        if sessions is not None:
            # if checking for jid from this data need to encode jid to utf-8
            return sessions
        else:
            return False

    def update_remote_session_data(self, user_jid, key, value, bot_id):
        remote_session_data = RedisCache(self.config).get_remote_session_data(user_jid, bot_id)
        if remote_session_data:
            remote_session_data[key] = value
            self.r.hset(str(bot_id) + "_remote_session_data", user_jid, json.dumps(remote_session_data))

    def add_remote_session_data(self, user_jid, user_ajid, remote_gjid, bot_id):
        remote_data = {"group_jid": remote_gjid, "user_ajid": user_ajid, "last_activity": time.time()}
        self.r.hset(str(bot_id) + "_remote_session_data", user_jid, json.dumps(remote_data))

    def get_remote_session_data(self, user_jid, bot_id):
        data = self.r.hget(str(bot_id) + "_remote_session_data", user_jid)
        if data:
            return json.loads(data)
        else:
            return False

    def remove_remote_session_data(self, user_jid, bot_id):
        self.r.hdel(str(bot_id) + "_remote_session_data", user_jid)

    def remove_all_from_remote_session(self, bot_id):
        self.r.delete(str(bot_id) + "_remote_session_data")

    # ------------------------------------
    #  Redis Cache - Media Substitution Queue
    # ------------------------------------

    def add_to_media_sub_queue(self, sub, response, action, sub_type, peer_jid, group_jid):
        sub_data = {"sub": sub, "response": response, "action": action, "type": sub_type, "time": time.time()}
        self.r.hset(group_jid + "_sub_queue", peer_jid, json.dumps(sub_data))

    def get_single_media_sub_queue(self, peer_jid, group_jid):
        sub_queue = self.r.hget(group_jid + "_sub_queue", peer_jid)
        result = json.loads(sub_queue)
        if result is not None:
            return result
        else:
            return None

    def get_all_media_sub_queue(self, group_jid):
        sub_queue = self.r.hgetall(group_jid + "_sub_queue")
        if sub_queue is not None:
            return sub_queue
        else:
            return None

    def rem_from_media_sub_queue(self, peer_jid, group_jid):
        self.r.hdel(group_jid + "_sub_queue", peer_jid)

    # ------------------------------------
    #  Redis Cache - Media Message Queue
    # ------------------------------------

    def add_to_media_message_queue(self, response, action, message_type, peer_jid, group_jid):
        sub_data = {"response": response, "action": action, "type": message_type, "time": time.time()}
        self.r.hset(group_jid + "_message_queue", peer_jid, json.dumps(sub_data))

    def get_single_media_message_queue(self, peer_jid, group_jid):
        sub_queue = self.r.hget(group_jid + "_message_queue", peer_jid)
        result = json.loads(sub_queue)
        if result is not None:
            return result
        else:
            return None

    def get_all_media_message_queue(self, group_jid):
        sub_queue = self.r.hgetall(group_jid + "_message_queue")
        if sub_queue is not None:
            return sub_queue
        else:
            return None

    def rem_from_media_message_queue(self, peer_jid, group_jid):
        self.r.hdel(group_jid + "_message_queue", peer_jid)

    # ------------------------------------
    #  Redis Cache - Heartbeat Cache
    # ------------------------------------

    def get_heartbeat_data(self, bot_id):
        heartbeat_data = self.r.hget(str(bot_id) + "_heartbeat", "heartbeat")
        if heartbeat_data:
            res = json.loads(heartbeat_data)
            return res
        else:
            return False

    def update_heartbeat_data(self, heartbeat_data, bot_id):
        self.r.hset(str(bot_id) + "_heartbeat", "heartbeat", json.dumps(heartbeat_data))

    def rem_heartbeat_data(self, bot_id):
        self.r.hdel(str(bot_id) + "_heartbeat", "heartbeat")

    # ------------------------------------
    #  Redis Cache - Group Censor Cache
    # ------------------------------------

    def add_censor_cache(self, peer_jid, group_jid):
        peer_data = {"warn_time": time.time()}
        self.r.hset(group_jid.split('@')[0] + "_censor_cache", peer_jid, json.dumps(peer_data))

    def get_all_censor_cache(self, group_jid):
        data = self.r.hgetall(group_jid.split('@')[0] + "_censor_cache")
        if data:
            return data
        else:
            return False

    def get_censor_cache(self, peer_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0] + "_censor_cache", peer_jid)
        if data:
            return json.loads(data)
        else:
            return False

    def rem_from_censor_cache(self, peer_jid, group_jid):
        self.r.hdel(group_jid.split('@')[0] + "_censor_cache", peer_jid)

    # ------------------------------------
    #  Redis Cache - Media Forward Queue
    # ------------------------------------

    def add_to_media_forward_queue(self, peer_jid, group_jid, bot_id):
        forward_data = {"group_jid": group_jid, "time": time.time()}
        self.r.hset(str(bot_id) + "_forward_queue", peer_jid, json.dumps(forward_data))

    def get_single_media_forward_queue(self, peer_jid, bot_id):
        sub_queue = self.r.hget(str(bot_id) + "_forward_queue", peer_jid)
        result = json.loads(sub_queue)
        if result is not None:
            return result
        else:
            return None

    def get_all_media_forward_queue(self, bot_id):
        sub_queue = self.r.hgetall(str(bot_id) + "_forward_queue")
        if sub_queue is not None:
            return sub_queue
        else:
            return None

    def rem_from_media_forward_queue(self, peer_jid, bot_id):
        self.r.hdel(str(bot_id) + "_forward_queue", peer_jid)

    # --------------------------------------
    #  Redis Cache - Group Command Cooldowns
    # --------------------------------------

    def add_to_group_cooldown(self, cooldown_name, group_jid):
        now = time.time()
        self.r.hset(group_jid + "_group_cooldown_queue", cooldown_name, now)

    def get_from_group_cooldown(self, cooldown_name, group_jid):
        cooldown_time = self.r.hget(group_jid + "_group_cooldown_queue", cooldown_name)
        if cooldown_time is not None:
            return cooldown_time
        else:
            return 0

    def remove_from_group_cooldown(self, cooldown_name, group_jid):
        self.r.hdel(group_jid + "_group_cooldown_queue", cooldown_name)

    def remove_all_group_cooldown(self, group_jid):
        self.r.delete(group_jid + "_group_cooldown_queue")

    # ------------------------------------
    #  Redis Cache - Group/User Activity History
    # ------------------------------------

    def add_single_history(self, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], "history")
        if data:
            data_json = json.loads(data)
            data_json[user_jid] = {"message": 0, "gif": 0, "image": 0, "video": 0}
            self.r.hset(group_jid.split('@')[0], "history", json.dumps(data_json))
        else:
            members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
            if members:
                RedisCache(self.config).add_all_history(members, group_jid)
                RedisCache(self.config).add_all_history(members, group_jid)

    def remove_single_history(self, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], "history")
        if data:
            data_json = json.loads(data)
            if user_jid in data_json:
                del data_json[user_jid]
                self.r.hset(group_jid.split('@')[0], "history", json.dumps(data_json))

    def set_single_history(self, type, user_jid, group_jid):
        data = self.r.hget(group_jid.split('@')[0], "history")
        if data:

            data_json = json.loads(data)
            if user_jid in data_json:
                data_json[user_jid][type] += 1
                self.r.hset(group_jid.split('@')[0], "history", json.dumps(data_json))
            else:
                RedisCache(self.config).add_single_history(user_jid, group_jid)
        else:
            members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
            if members:
                RedisCache(self.config).add_all_history(members, group_jid)
                RedisCache(self.config).add_all_history(members, group_jid)

    def get_all_history(self, group_jid):
        data = self.r.hget(group_jid.split('@')[0], "history")
        if data:
            data_json = json.loads(data)
            return data_json
        else:
            return False

    def add_all_history(self, member_list, group_jid):
        data = {}
        for m in member_list:
            data[m] = {"message": 0, "gif": 0, "image": 0, "video": 0}
        self.r.hset(group_jid.split('@')[0], "history", json.dumps(data))

    def reset_all_history(self, group_jid):
        self.r.delete(group_jid.split('@')[0], "history")
        members = json.loads(self.r.hget(group_jid.split('@')[0], "group_members"))
        if members:
            RedisCache(self.config).add_all_history(members, group_jid)

    def remove_all_history(self, group_jid):
        self.r.delete(group_jid.split('@')[0], "history")
