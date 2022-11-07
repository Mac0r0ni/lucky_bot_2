import time

from lib.database_handler import Database
from lib.message_processing_handler import process_message, MessageProcessing
from lib.redis_handler import RedisCache


class User:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username

    def user_join_group(self, response, invite_status):
        display_name = response.status.split(" has joined the ")[0].rstrip()
        group_data = RedisCache(self.config).get_all_group_data(response.group_jid)

        if Database(self.config).check_for_group(response.group_jid) is True:
            group_status = 1
            group_settings = group_data["group_settings"]
            group_messages = group_data["group_messages"]
            group_admins = group_data["group_admins"]
        else:
            group_status = 0
            group_settings = False
            group_messages = False
            group_admins = False

        # put user in last joiner cache
        peer_data = {"display_name": display_name, "group_jid": response.group_jid,
                     "alias_jid": response.status_jid,
                     "user_jid": "Unknown", "verified": 0,
                     "join_time": time.time(), "timeout": 0}
        RedisCache(self.config).add_to_last_queue("joiner", peer_data, response.group_jid)

        # add user as friend to get data for name grab
        if group_settings["grab_status"] == 1:
            RedisCache(self.config).add_to_grab_queue(display_name, response.group_jid, self.bot_id)
            self.client.add_friend(response.status_jid)

        if invite_status == 0:
            if group_status == 1:
                if group_settings["lock_status"] == 1:
                    print("lock on")
                    if group_messages["lock_message"] != "none":
                        # process lock_message
                        # send lock_message
                        lock_message = process_message(self.config, "join_pre_queue", group_messages["lock_message"], display_name,
                                                       response.group_jid, self.bot_id, "0")
                        self.client.send_chat_message(response.group_jid, lock_message)

                    self.client.remove_peer_from_group(response.group_jid, response.status_jid)
                    return
                else:
                    if group_settings["cap_status"] == 1:
                        # see if we need to remove last active
                        print("cap_check")
                        # admintools.UserCap(self.client).remove_last_active(response, bot_name, bot_id)

                    # send peer data to redis join_queue cache
                    RedisCache(self.config).add_to_join_queue(response.status_jid, peer_data, self.bot_id)

                    # get user info by ajid using xiphias (xiphias gives us account days)
                    self.client.xiphias_get_users_by_alias(response.status_jid)

        elif invite_status == 1:
            if group_status == 1:
                if group_settings["lock-invite_status"] == 1:
                    print("invites are locked")
                    inviter = response.status.split("invited by ")[1]
                    admin_invite = 0

                    # check if the person inviting was an admin
                    if group_admins:
                        for ad in group_admins:
                            if group_admins[ad] == inviter:
                                admin_invite = 1

                    if admin_invite == 0:
                        # person inviting was not an admin
                        if group_messages["lock-invite_message"] != "none":
                            # process lock invite message
                            # send lock invite message
                            lock_message = process_message(self.config, "join_pre_queue", group_messages["lock-invite_message"],
                                                           display_name, response.group_jid, self.bot_id, "0")
                            self.client.send_chat_message(response.group_jid, lock_message)
                        self.client.remove_peer_from_group(response.group_jid, response.status_jid)
                        return
                # check invite-verification (do invited users need to verify?)
                if group_settings["invite-verification_status"] == 1:
                    # Check cap status
                    if group_settings["cap_status"] == 1:
                        # see if we need to remove last active
                        print("cap_check")

                    # we send user to verification here

                    # send peer data to redis join_queue cache
                    RedisCache(self.config).add_to_join_queue(response.status_jid, peer_data, self.bot_id)

                    if response.group.is_public:
                        # if public group we request by alias_jid
                        self.client.xiphias_get_users_by_alias(response.status_jid)
                    else:
                        # if private group we request by jid
                        self.client.xiphias_get_users(response.status_jid)
                else:
                    # Check cap status
                    if group_settings["cap_status"] == 1:
                        # see if we need to remove last active
                        print("cap_check")

                    # user was invited and no invite verification
                    if group_settings["welcome_status"] == 1:
                        print("Welcome Enabled")
                        if group_messages["welcome_message"] != "none":
                            print("Welcome Message Send")
                            # process_message_media(self.client, "welcome_message_pre", group_messages["welcome_message"], display_name, response.group_jid)

                            MessageProcessing(self).process_message_media("welcome_message_pre",
                                                                          group_messages["welcome_message"],
                                                                          response.status_jid,
                                                                          response.group_jid)
            # Next we update group owner/admins/members we do this on every join to keep database up to date.
            if response.group.is_public:
                scope = "public"
                group_hash = response.group.code.lower()
            else:
                scope = "private"
                group_jid_to_hash = str(response.group_jid).split("_g@")[0][-8:]
                group_hash = "#"
                for x in group_jid_to_hash:
                    group_hash += str(chr(ord('`') + int(x) + 1))

            if response.group.name:
                group_name = response.group.name
            else:
                group_name = "Unknown"

            # add joining user to data from kik
            obj = type('', (), {})()
            obj.jid = response.status_jid
            obj.is_admin = 0
            obj.is_owner = 0
            response.group.members.append(obj)

            group_members_list = []
            for m in response.group.members:
                group_members_list.append(m.jid)
                if m.jid != response.to_jid:
                    if group_settings:
                        if group_settings["grab_status"] == 1:
                            if m.jid != response.status_jid:
                                self.client.add_friend(m.jid)
                        else:
                            self.client.add_friend(m.jid)
                    else:
                        self.client.add_friend(m.jid)

            if "talkers" not in group_data:
                RedisCache(self.config).add_all_talker_lurker("talkers", group_members_list, response.group_jid)
            if "lurkers" not in group_data:
                RedisCache(self.config).add_all_talker_lurker("lurkers", group_members_list, response.group_jid)

            RedisCache(self.config).add_single_talker_lurker("talkers", response.status_jid, response.group_jid)
            RedisCache(self.config).add_single_talker_lurker("lurkers", response.status_jid, response.group_jid)

            time.sleep(2.5)

            # if group is more than 50 users we need to split to 2 requests
            if len(group_members_list) > 50:
                length = len(group_members_list)
                middle_index = (length // 2)
                first_half = group_members_list[:middle_index]
                second_half = group_members_list[middle_index:]

                info_id_1 = self.client.request_info_of_users(first_half)
                info_id_2 = self.client.request_info_of_users(second_half)

            else:
                info_id_1 = self.client.request_info_of_users(group_members_list)
                info_id_2 = "None"

            # add to group queue to let user data come back.
            RedisCache(self.config).add_to_group_queue_cache(scope, info_id_1, info_id_2, group_hash, group_name,
                                                             self.bot_id,
                                                             group_status,
                                                             response.group.owner,
                                                             response.group.admins, response.group.members,
                                                             response.group_jid)

    def group_user_remove(self, peer_jid, group_jid):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        members = group_data["group_members"]
        group_admins = group_data["group_admins"]

        join_queue = RedisCache(self.config).get_all_join_queue(self.bot_id)
        peer_data_queue = RedisCache(self.config).get_all_peer_data(self.bot_id)


        if peer_data_queue:
            if members[peer_jid]["display_name"].encode('utf-8') in peer_data_queue:
                print("deleting member peer data")
                RedisCache(self.config).remove_peer_data(members[peer_jid]["display_name"], self.bot_id)

        if join_queue:
            if peer_jid.encode('utf-8') in join_queue:
                RedisCache(self.config).remove_from_join_queue(peer_jid, self.bot_id)

        if group_admins:
            if peer_jid in group_admins:
                del group_admins[peer_jid]
                Database(self.config).update_group_data("json", "group_admins", group_admins, group_jid)
        if members:
            if peer_jid in members:
                del members[peer_jid]
                Database(self.config).update_group_data("json", "group_members", members, group_jid)

    def promote_user_to_admin(self, response):
        group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
        group_admins = group_data["group_admins"]
        if response.status_jid not in group_admins:
            status_text = response.status.split("to admin")[0].rstrip()
            display_name = status_text.split("has promoted ")[1].rstrip()
            group_admins[response.status_jid] = display_name
            Database(self.config).update_group_data("json", "group_admins", group_admins, response.group_jid)
            self.client.send_chat_message(response.group_jid, "Promoted: " + display_name)

    def demote_user_from_admin(self, response):
        group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
        group_admins = group_data["group_admins"]
        if response.status_jid in group_admins:
            display_name = response.status.split(" has removed admin status from ")[1].rstrip()
            del group_admins[response.status_jid]
            Database(self.config).update_group_data("json", "group_admins", group_admins, response.group_jid)
            self.client.send_chat_message(response.group_jid, "Demoted: " + display_name)


