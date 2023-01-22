import time

from colorama import Fore, Style

from lib.redis_handler import RedisCache


class StickerResponse:
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

    def parse_sticker_response(self, response):
        # Sticker Response
        if not response.group_jid:
            # PM Sticker Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM Sticker Response" + Style.RESET_ALL)
        else:
            # Group Sticker Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "Group Sticker Response" + Style.RESET_ALL)

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