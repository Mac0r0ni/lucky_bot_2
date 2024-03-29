from colorama import Fore, Style

from lib.database_handler import Database
from lib.message_processing_handler import MessageProcessing
from lib.redis_handler import RedisCache
from lib.user_handler import User


class GroupStatus:
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

    def parse_group_status(self, response):
        group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
        if not group_data:
            return
        group_members = group_data["group_members"]
        print(self.debug + f"Status message in {response.group_jid}: {response.status}")

        status = response.status.lower()

        if "changed the group name" in status:
            GroupStatus(self).process_group_name_change(response)

        if "promoted" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "Promoted User")
            User(self).promote_user_to_admin(response)
            return
        if "removed admin" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "Demoted User")
            User(self).demote_user_from_admin(response)
            return

        if "you have been promoted to owner" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "I am the owner.")
            # If we are group owner leave automatically
            self.client.leave_group(response.group_jid)

        if "invite" not in status and " has joined" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User Join From Hash")
            User(self).user_join_group(response, 0)
            return
        elif "invite" in status and " has joined" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User joined from invite, link, or code.")
            User(self).user_join_group(response, 1)
            return
        elif "has left the chat" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User left chat.")
            if group_data["group_settings"]["exit_status"] == 1:
                if group_data["group_messages"]["exit_message"] != "none":
                    MessageProcessing(self).process_message_media("exit_message", group_data["group_messages"]["exit_message"], response.status_jid, response.group_jid)
            if group_members:
                if response.status_jid in group_members:
                    if group_members[response.status_jid]["jid"] != "Unknown":
                        peer_data = {"display_name": group_members[response.status_jid]["display_name"], "group_jid": response.group_jid,
                                     "alias_jid": response.status_jid,
                                     "user_jid": group_members[response.status_jid]["jid"]}
                        RedisCache(self.config).add_to_last_queue("leave", peer_data, response.group_jid)
            User(self).group_user_remove(response.status_jid, response.group_jid)
            return
        elif "has removed" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User was removed")
            if group_members:
                if response.status_jid in group_members:
                    if group_members[response.status_jid]["jid"] != "Unknown":
                        peer_data = {"display_name": group_members[response.status_jid]["display_name"], "group_jid": response.group_jid,
                                     "alias_jid": response.status_jid,
                                     "user_jid": group_members[response.status_jid]["jid"]}
                        RedisCache(self.config).add_to_last_queue("kick", peer_data, response.group_jid)
            User(self).group_user_remove(response.status_jid, response.group_jid)
            return
        elif "has banned" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User was banned")
            if group_members:
                if response.status_jid in group_members:
                    if group_members[response.status_jid]["jid"] != "Unknown":
                        peer_data = {"display_name": group_members[response.status_jid]["display_name"], "group_jid": response.group_jid,
                                     "alias_jid": response.status_jid,
                                     "user_jid": group_members[response.status_jid]["jid"]}
                        RedisCache(self.config).add_to_last_queue("ban", peer_data, response.group_jid)
            User(self).group_user_remove(response.status_jid, response.group_jid)
            return
        elif "has unbanned" in status:
            if self.config["general"]["debug"] >= 1:
                print(self.debug + "User was unbanned")
            return
        else:
            return

    def process_group_name_change(self, response):
        group_name = response.status.split("group name to ")[1]
        Database(self.config).update_group_data("str", "group_name", group_name, response.group_jid)
        self.client.send_chat_message(response.group_jid, "Group name changed to: " + group_name)
        if self.config["general"]["debug"] >= 1:
            print(self.debug + "Group Name Changed to: " + group_name)
        return
