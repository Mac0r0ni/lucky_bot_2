import time

from lib.database_handler import Database
from lib.redis_handler import RedisCache


class GroupInitUpdate:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name
        self.bot_username = client.bot_username

    def update_add_database(self, scope, group_hash, group_name, group_status, owner, admins, members,
                            group_jid, bot_id):
        if group_status == 1:
            # group already in database, we are just updating name/owner/members/admins
            Database(self.config).update_group_database(group_jid, group_name, owner, admins, members)

        elif group_status == 0:
            # group not in database, need to create an entry
            if scope == "public":
                join_time = time.time()
            elif scope == "private":
                join_time = time.time() - 43500
            else:
                join_time = time.time()

            # Group Doesn't exist in Database, Create it
            # Create Settings and Messages Default
            group_settings = {"join_time": join_time, "group_language": 0, "lock_status": 0, "welcome_status": 1,
                              "invite-verification_status": 0, "lock-invite_status": 0, "silent-join_status": 0,
                              "silent-join_time": 120, "federation_status": 0, "federation_id": 0, "global-ban_status": 1,
                              "global-ban_max": 5, "exit_status": 0, "search_status": 0, "lucky-bomb_status": 0,
                              "verification_status": 1, "verification_time": 120, "verification_days": 9999,
                              "noob_status": 1, "noob_days": 10, "media-forward_status": 0, "trigger_status": 2,
                              "rank_status": 0, "profile_status": 1, "grab_status": 0, "censor_status": 0,
                              "censor_time": 1800, "cap_status": 0, "cap_users": 98, "bot-helper_status": 0, "casino_status": 0,
                              "slots_jackpot": 500,
                              "roast_status": 0, "confessions_status": 0, "dice_default": 6, }
            group_messages = {"welcome_message": "Welcome!", "lock_message": "Group is Locked",
                              "exit_message": "Bye $u",
                              "global-ban_message": "$u, You have too many global bans to join. $gb bans!",
                              "verification_message": "Please type “not a bot“ to verify you are not a bot.",
                              "verification_phrase": "not a bot",
                              "verification_ended_message": "Please come back when you can verify.",
                              "verification_wrong_message": "Incorrect, try again.",
                              "noob_message": "Account not old enough to join. $d days.",
                              "silent-join_message": "Removing silent user.",
                              "cap_message": "Removing last active.",
                              "purge_message": "Removing for inactivity, please rejoin when you are more active.",
                              "profile_message": "A profile picture is required. Please set one and join back.",
                              "lock-invite_message": "Invites are off for this group. Join normally with $gh",
                              "timer_message": "Ding", "censor-warn_message": "Warning! $cw is censored, if you say it again you will be removed, $u", "censor-kick_message": "I told you not to say it..."}

            user_triggers = {}
            admin_triggers = {}

            # remove existing talkers/lurkers
            RedisCache(self.config).remove_all_talker_lurkers("talkers", group_jid)
            RedisCache(self.config).remove_all_talker_lurkers("lurkers", group_jid)

            # create talkers/lurkers data
            RedisCache(self.config).add_all_talker_lurker("talkers", members, group_jid)
            RedisCache(self.config).add_all_talker_lurker("lurkers", members, group_jid)


            Database(self.config).add_group_to_database(group_jid, group_hash, group_name, group_settings, group_messages,
                                             owner, admins, members, user_triggers, admin_triggers, bot_id)

            self.client.send_chat_message(group_jid, "Done Initializing Database!")

            Database(self.config).load_single_group_cache(group_jid)