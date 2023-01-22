import time

from colorama import Fore, Style

from lib.database_handler import Database
from lib.redis_handler import RedisCache


class GroupSysMessage:
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

    def group_sys_message_parser(self, response):
        if self.config["general"]["debug"] == 1:
            print(Fore.GREEN + Style.BRIGHT + "[+] System message in {}: {}".format(response.group_jid,
                                                                                    response.sysmsg) + Style.RESET_ALL)

        if 'As a new member of this group' in response.sysmsg:
            kikjail_1 = response.sysmsg.split("emojis. In ")
            kikjail_2 = kikjail_1[1].split(" you can share pictures")
            self.client.send_chat_message(response.group_jid, "I am unable to send pictures, videos, or links because "
                                                              "of kik jail for another " + kikjail_2[0] + ".")
            return

        elif 'added you' in response.sysmsg:
            print(Fore.GREEN + Style.BRIGHT + "[+] I have been added to the group {}".format(response.group_jid
                                                                                             ) + Style.RESET_ALL)

            # get bot data from cache
            bot_data = RedisCache(self.config).get_all_bot_config_data(self.bot_id)

            if response.group.is_public:
                scope = "public"
                group_hash = response.group.code.lower()

            else:
                scope = "private"
                group_jid_to_hash = str(response.group_jid).split("_g@")[0][-8:]
                group_hash = "#"
                for x in group_jid_to_hash:
                    group_hash += str(chr(ord('`') + int(x) + 1))

            if bot_data["bot_settings"]["whitelist"] == 1:
                group_whitelist = bot_data["bot_whitelist_groups"]
                if response.group_jid not in group_whitelist:
                    if group_hash not in group_whitelist:
                        print("Not in Whitelist?")
                        self.client.leave_group(response.group_jid)
                        return

            if bot_data["bot_settings"]["blacklist"] == 1:
                group_blacklist = bot_data["bot_blacklist_groups"]
                if response.group_jid in group_blacklist or group_hash in group_blacklist:
                    self.client.leave_group(response.group_jid)
                    return

            count = Database(self.config).get_bot_group_count(self.bot_id)
            print(count)
            if count >= self.config["general"]["max_groups"]:
                self.client.send_chat_message(response.group_jid, "I am at max groups. Later boners!")
                self.client.leave_group(response.group_jid)
                return

            group_name = response.group.name

            # Initialize Group Data
            self.client.send_chat_message(response.group_jid, "Initializing Group Database....")

            if Database(self.config).check_for_group(response.group_jid) is True:
                Database(self.config).remove_group(response.group_jid)

            # modify response object and add bot to it as a member
            obj = type('', (), {})()
            obj.jid = response.to_jid
            obj.is_admin = 0
            obj.is_owner = 0
            response.group.members.append(obj)

            group_members_list = []
            for m in response.group.members:
                group_members_list.append(m.jid)
                if m.jid != response.to_jid:
                    self.client.add_friend(m.jid)

            time.sleep(2.5)
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

            RedisCache(self.config).add_to_group_queue_cache(scope, info_id_1, info_id_2, group_hash, group_name, self.bot_id, 0,
                                                  response.group.owner,
                                                  response.group.admins, response.group.members, response.group_jid)

        elif 'You have been removed from the group' in response.sysmsg:
            print(Fore.RED + Style.BRIGHT + "[+] I have been removed from the group {}".format(response.group_jid
                                                                                               ) + Style.RESET_ALL)
            Database(self.config).remove_group(response.group_jid)
            RedisCache(self.config).remove_from_group_queue(response.group_jid, self.bot_id)
            return
