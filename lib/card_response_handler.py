import time

from colorama import Fore, Style

from lib.redis_handler import RedisCache


class CardResponse:
    def __init__(self, client):
        self.client = client.client
        self.callback = client
        self.config = client.config
        self.bot_id = client.bot_id
        self.bot_display_name = client.bot_display_name

    def parse_card_response(self, response):
        # Card Response
        if not response.group_jid:
            # PM Card Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "PM Card Response" + Style.RESET_ALL)
        else:
            # Group Card Response
            if self.config["general"]["debug"] == 1:
                print(Fore.LIGHTRED_EX + "Group Card Response" + Style.RESET_ALL)

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

