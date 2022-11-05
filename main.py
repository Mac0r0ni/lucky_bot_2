#!/usr/bin/env python3


# Python 3 Core Libraries
import json
import logging
import sys
import time
import platform
from threading import Thread
from random import uniform

# Python 3 Third Party Libraries
from colorama import Fore, Style, init
import kik_unofficial.datatypes.xmpp.chatting as chatting
from kik_unofficial.client import KikClient
from kik_unofficial.callbacks import KikClientCallback
from kik_unofficial.datatypes.xmpp.errors import *
from kik_unofficial.datatypes.xmpp.login import *
from kik_unofficial.datatypes.xmpp.roster import *
from kik_unofficial.datatypes.xmpp.sign_up import *
from kik_unofficial.datatypes.xmpp.xiphias import *
from kik_unofficial.datatypes.xmpp.group_adminship import *

# Python 3 Project Libraries
import lib.bot_config_handler as bot_config
from lib.card_response_handler import CardResponse
from lib.database_handler import Database
from lib.gif_response_handler import GifResponse
from lib.group_message_handler import GroupMessage
from lib.group_status_handler import GroupStatus
from lib.image_response_handler import ImageResponse
from lib.peer_info_handler import PeerInfo
from lib.private_message_handler import PrivateMessage
from lib.redis_handler import RedisCache
from lib.sticker_response_handler import StickerResponse
from lib.system_message_handler import GroupSysMessage
from lib.video_response_handler import VideoResponse

if platform.system() == "Windows":
    # Init Colorama for Windows
    init()

main_config = open('etc/bot_config.json', 'r')
config_data = json.load(main_config)


def main():
    bot = LuckyBot()


class LuckyBot(KikClientCallback):
    def __init__(self):
        bot_configuration = bot_config.get_bot(sys.argv[1])
        print(bot_configuration[0].password)
        self.client = KikClient(self,
                                kik_username=bot_configuration[0].username,
                                kik_password=bot_configuration[0].password,
                                device_id_override=bot_configuration[0].device_id,
                                android_id_override=bot_configuration[0].android_id,
                                operator_override=bot_configuration[0].operator,
                                brand_override=bot_configuration[0].brand,
                                model_override=bot_configuration[0].model,
                                android_sdk_override=bot_configuration[0].android_sdk,
                                install_date_override=bot_configuration[0].install_date,
                                logins_since_install_override=bot_configuration[0].logins_since_install,
                                registrations_since_install_override=bot_configuration[0].registrations_since_install)

        self.bot_username = bot_configuration[0].username
        self.bot_display_name = ""
        self.bot_id = bot_configuration[0].bot_id
        self.config = config_data

    # --------------------------------------------
    #  API - Login/Authentication Event Listeners
    # --------------------------------------------

    def on_authenticated(self):
        print(Fore.GREEN + Style.BRIGHT + "Now I'm Authenticated" + Style.RESET_ALL)

    def on_login_ended(self, response: LoginResponse):
        print(Fore.RED + Style.BRIGHT + "Full name: {} {}".format(response.first_name, response.last_name)
              + Style.RESET_ALL)

        self.bot_display_name = response.first_name + " " + response.last_name
        print(Fore.GREEN + "Loading All Groups Cache" + Style.RESET_ALL)
        gcloading = time.time()
        Database(self.config).load_all_bot_groups_to_cache(self.bot_id)
        Database(self.config).load_bot_data_to_cache(self.bot_id)
        print(Fore.GREEN + "Finished Loading groups Cache in " + str(
            time.time() - gcloading) + " seconds." + Style.RESET_ALL)


    # ------------------------------------
    #  API - PM Event Listeners
    # ------------------------------------

    # Listener for Private Messages
    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        PrivateMessage(self).private_message_parser(chat_message)
        return

    # Listener for Is Typing in PM
    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):

        if self.config["general"]["debug"] == 2:
            print(Fore.YELLOW + "[+] {} is now {}typing.".format(response.from_jid,
                                                                 "not " if not response.is_typing else "") + Style.RESET_ALL)
        return

    # Listener for Message Delivered for PM
    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):

        if self.config["general"]["debug"] == 2:
            print(Fore.LIGHTMAGENTA_EX + "[+] Chat message with ID {} is delivered.".format(
                response.message_id) + Style.RESET_ALL)
        return

    # Listener for Message Read for PM
    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        if self.config["general"]["debug"] == 2:
            print(Fore.LIGHTMAGENTA_EX + "[+] Human has read the message with ID {}.".format(
                response.message_id) + Style.RESET_ALL)
        return

    # ------------------------------------
    #  API - Group Event Listeners
    # ------------------------------------

    # Listener for Group Message Read/Delivered
    def on_group_receipts_received(self, response: chatting.IncomingGroupReceiptsEvent):
        if self.config["general"]["debug"] == 2:
            print(Fore.LIGHTMAGENTA_EX + "[+] Message with ID {} has been {}".format(
                response.message_id, response.type) + Style.RESET_ALL)
            group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
            if not group_data:
                return
            if "lurkers" in group_data:
                RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), response.from_jid, response.group_jid)
            else:
                if "group_members" in group_data:
                    RedisCache(self.config).add_all_talker_lurker("lurkers", group_data["group_members"], response.group_jid)
            return
        return

    # Listener for Group Messages
    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage):
        GroupMessage(self).group_message_parser(chat_message)
        return

    # Listener for Group Typing Events
    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        if self.config["general"]["debug"] == 2:
            print(Fore.LIGHTYELLOW_EX + "[+] {} is now {}typing in group {}".format(response.from_jid,
                                                                                    "not " if not response.is_typing else "",
                                                                                    response.group_jid) + Style.RESET_ALL)
        return

    # Listener for when a group Status Message as been received.
    def on_group_status_received(self, response: chatting.IncomingGroupStatus):
        GroupStatus(self).parse_group_status(response)
        return

    # Listener for when a group System Message as been received.
    def on_group_sysmsg_received(self, response: chatting.IncomingGroupSysmsg):
        GroupSysMessage(self).group_sys_message_parser(response)
        return

    # ------------------------------------
    #  API - Media Event Listeners
    # ------------------------------------

    # Listener for when Image received from group or PM
    def on_image_received(self, response: chatting.IncomingImageMessage):
        ImageResponse(self).parse_image_response(response)

    # Listener for when Video received, group or PM
    def on_video_received(self, response: chatting.IncomingVideoMessage):
        VideoResponse(self).parse_video_response(response)
        return

    # Listener for when GIF received, group or PM
    def on_gif_received(self, response: chatting.IncomingGifMessage):
        GifResponse(self).parse_gif_response(response)
        return

    # Listener for when Card received, group or PM
    def on_card_received(self, response: chatting.IncomingCardMessage):
        CardResponse(self).parse_card_response(response)
        return

    # Listener for when Sticker received, group or PM
    def on_group_sticker(self, response: chatting.IncomingGroupSticker):
        StickerResponse(self).parse_sticker_response(response)
        return

    # ------------------------------------
    #  API - Peer Info Event Listeners
    # ------------------------------------

    # Listener for when Peer Info received.
    def on_peer_info_received(self, response: PeersInfoResponse):
        PeerInfo(self).peer_info_parser(response)

    # Listener for when Peer Info received through Xiphias request.
    def on_xiphias_get_users_response(self, response: Union[UsersResponse, UsersByAliasResponse]):
        PeerInfo(self).xiphias_info_parser(response)

    # ------------------------------------
    #  API - Misc Event Listeners
    # ------------------------------------

    def on_status_message_received(self, response: chatting.IncomingStatusResponse):
        if self.config["general"]["debug"] == 1:
            print(Fore.YELLOW + "[+] Status message from {}: {}".format(response.from_jid,
                                                                        response.status) + Style.RESET_ALL)
        return

    def on_username_uniqueness_received(self, response: UsernameUniquenessResponse):
        if self.config["general"]["debug"] == 1:
            print("Is {} a unique username? {}".format(response.username, response.unique))
        return

    def on_sign_up_ended(self, response: RegisterResponse):
        if self.config["general"]["debug"] == 1:
            print("[+] Registered as " + response.kik_node)
        return

    # Listener for when group search is received.
    def on_group_search_response(self, response: GroupSearchResponse):
        if self.config["general"]["debug"] == 1:
            print(Fore.MAGENTA + "[+] Search Response: {}" + str(response.groups) + Style.RESET_ALL)
        return

    # Listener for when roster is received.
    def on_roster_received(self, response: FetchRosterResponse):
        if self.config["general"]["debug"] == 1:
            print(Fore.YELLOW + "[+] Chat partners:\n" + '\n'.join(
                [str(member) for member in response.peers]) + Style.RESET_ALL)
        return

    # Listener for friend attributions
    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        if self.config["general"]["debug"] == 1:
            print(
                Fore.LIGHTYELLOW_EX + "[+] Friend attribution request from " + response.referrer_jid + Style.RESET_ALL)
        return

    # ------------------------------------
    #  API - Error Event Listeners
    # ------------------------------------

    def on_connection_failed(self, response: ConnectionFailedResponse):
        print("[-] Connection failed: " + response.message)
        return

    def on_login_error(self, login_error: LoginError):
        #print(f'[-] Login Error: {login_error.error_code}, {login_error.error_messages}')
        return

    def on_temp_ban_received(self, response: TempBanElement):
        print(f'[-] Temporary Ban: {response.ban_title}, {response.ban_message}\nEnds: {response.ban_end_time}')
        return

    def on_register_error(self, response: SignUpError):
        print("[-] Register error: {}".format(response.message))
        return


if __name__ == '__main__':
    main()
    logging.basicConfig(format=KikClient.log_format(), level=logging.INFO)
