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
from colorama import Fore, Style, init, Back
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
from lib.email_handler import send_email
from lib.gif_response_handler import GifResponse
from lib.group_message_handler import GroupMessage
from lib.group_status_handler import GroupStatus
from lib.heartbeat_handler import heartbeat_loop
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
        self.bot_username = bot_configuration[0].username
        self.bot_display_name = ""
        self.bot_id = bot_configuration[0].bot_id
        self.config = config_data
        self.debug = f'[' + Style.BRIGHT + Fore.MAGENTA + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.GREEN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '
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

    # --------------------------------------------
    #  API - Login/Authentication Event Listeners
    # --------------------------------------------

    def on_authenticated(self):
        print(self.info + f'Authenticated' + Style.RESET_ALL)
        self.client.request_roster()

        heartbeat_data = RedisCache(self.config).get_heartbeat_data(self.bot_id)
        if heartbeat_data:
            if heartbeat_data["offline"] and heartbeat_data['recovered'] is False:
                heartbeat_data["offline"] = False
                heartbeat_data["recovered"] = True
                heartbeat_data["time"] = time.time()
                if heartbeat_data["captcha"]:
                    heartbeat_data["captcha"] = False
                if heartbeat_data["temp_ban"]:
                    heartbeat_data["temp_ban"] = False
                    heartbeat_data["temp_ban_time"] = 0
            RedisCache(self.config).update_heartbeat_data(heartbeat_data, self.bot_id)
        Thread(target=heartbeat_loop, args=(self.client, self.config, self.bot_id,)).start()

    def on_login_ended(self, response: LoginResponse):
        print(self.info + f'Full name: {response.first_name} {response.last_name}' + Style.RESET_ALL)

        self.bot_display_name = response.first_name + " " + response.last_name
        print(self.info + f'Loading All Groups Cache' + Style.RESET_ALL)
        gcloading = time.time()
        Database(self.config).load_all_bot_groups_to_cache(self.bot_id)
        Database(self.config).load_bot_data_to_cache(self.bot_id)
        print(self.info + f'Finished Loading groups Cache in {str(time.time() - gcloading)} seconds.' + Style.RESET_ALL)

    # ------------------------------------
    #  API - PM Event Listeners
    # ------------------------------------

    # Listener for Private Messages
    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        PrivateMessage(self).private_message_parser(chat_message)
        return

    # Listener for Is Typing in PM
    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):

        if self.config["general"]["debug"] >= 2:
            if not response.is_typing:
                print(self.debug + f'{response.from_jid} is now not typing.' + Style.RESET_ALL)
            else:
                print(self.debug + f'{response.from_jid} is now typing.' + Style.RESET_ALL)

        return

    # Listener for Message Delivered for PM
    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):

        if self.config["general"]["debug"] >= 2:
            print(self.debug + f'Chat message with ID {response.message_id} is delivered.' + Style.RESET_ALL)

        return

    # Listener for Message Read for PM
    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        if self.config["general"]["debug"] >= 2:
            print(self.debug + f'Human has read the message with ID {response.message_id}.' + Style.RESET_ALL)
        return

    # ------------------------------------
    #  API - Group Event Listeners
    # ------------------------------------

    # Listener for Group Message Read/Delivered
    def on_group_receipts_received(self, response: chatting.IncomingGroupReceiptsEvent):
        if self.config["general"]["debug"] >= 2:
            print(self.debug + f'Message with ID {response.message_id} has been {response.type}.' + Style.RESET_ALL)
            group_data = RedisCache(self.config).get_all_group_data(response.group_jid)
            if not group_data:
                return
            if "lurkers" in group_data:
                RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), response.from_jid,
                                                                 response.group_jid)
            else:
                if "group_members" in group_data:
                    RedisCache(self.config).add_all_talker_lurker("lurkers", group_data["group_members"],
                                                                  response.group_jid)
                    RedisCache(self.config).set_single_talker_lurker("lurkers", time.time(), response.from_jid,
                                                                     response.group_jid)
            return
        return

    # Listener for Group Messages
    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage):
        GroupMessage(self).group_message_parser(chat_message)
        return

    # Listener for Group Typing Events
    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        if self.config["general"]["debug"] >= 2:
            if not response.is_typing:
                print(self.debug + f'{response.from_jid} is now not typing in group {response.group_jid}.' + Style.RESET_ALL)
            else:
                print(self.debug + f'{response.from_jid} is now typing in group {response.group_jid}.' + Style.RESET_ALL)

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

    # Listener for when Peer Info or Xiphias request has an error.
    def on_peer_info_error(self, response: PeersInfoError):
        print(self.critical + "Peer Response Error: " + str(response.error_code))
        join_queue_users = RedisCache(self.config).get_all_join_queue(self.bot_id)
        for x in join_queue_users:
            join_data = json.loads(join_queue_users[x].decode("utf-8"))
            if "peer_info_request_id" in join_data:
                if join_data["peer_info_request_id"] == response.message_id:
                    user_join_info = RedisCache(self.config).get_single_join_queue(x.decode('utf-8'), self.bot_id)
                    print(self.warning + "Error From User Request: " + str(user_join_info["display_name"]))
                    request_type = user_join_info["peer_info_request_type"]
                    request_jid = user_join_info["alias_jid"]
                    request_tries = int(user_join_info["peer_info_request_tries"])
                    if request_tries <= 4:
                        if request_type == "xpub":
                            print(self.warning + "Retrying Peer Info Request")
                            message_id = self.client.xiphias_get_users_by_alias(request_jid)
                            user_join_info["peer_info_request_tries"] += 1
                            user_join_info["peer_info_request_id"] = message_id
                            RedisCache(self.config).add_to_join_queue(request_jid, user_join_info, self.bot_id)
                            return
                        elif request_type == "xpri":
                            print(self.warning + "Retrying Peer Info Request")
                            message_id = self.client.xiphias_get_users(request_jid)
                            user_join_info["peer_info_request_tries"] += 1
                            user_join_info["peer_info_request_id"] = message_id
                            RedisCache(self.config).add_to_join_queue(request_jid, user_join_info, self.bot_id)
                            return
                        else:
                            print(self.critical + "Unknown Request Type")
                            return
                    else:
                        RedisCache(self.config).remove_from_join_queue(request_jid, self.bot_id)
                        print(self.critical + "Peer Info Request Failed 5 times. Removing user from join queue.")
                        return
        group_queue = RedisCache(self.config).get_group_queue(self.bot_id)
        for x in group_queue:
            group_data = json.loads(group_queue[x].decode("utf-8"))
            if "info_id_1" in group_data and "info_id_2" in group_data:
                if group_data["info_id_1"] == response.message_id:
                    group_queue_data = RedisCache(self.config).get_single_group_queue(x.decode('utf-8'), self.bot_id)
                    print(self.warning + "Error From Group Request: " + str(group_queue_data["group_name"]))
                    request_tries = int(group_queue_data["info_1_tries"])
                    if request_tries <= 4:
                        print(self.warning + "Retrying Group Info Request")
                        message_id = self.client.request_info_of_users(group_queue_data["info_request_1"])
                        request_tries += 1
                        RedisCache(self.config).update_group_queue_json("info_1_tries", request_tries, x.decode('utf-8'), self.bot_id)
                        RedisCache(self.config).update_group_queue_json("info_id_1", message_id,
                                                                        x.decode('utf-8'), self.bot_id)
                        return
                    else:
                        RedisCache(self.config).remove_from_group_queue(x.decode('utf-8'), self.bot_id)
                        print(self.critical + "Group Info Request Failed 5 times. Removing group from group queue.")
                        return

                elif group_data["info_id_2"] == response.message_id:
                    group_queue_data = RedisCache(self.config).get_single_group_queue(x.decode('utf-8'), self.bot_id)
                    print(self.warning + "Error From Group Request: " + str(group_queue_data["group_name"]))
                    request_tries = int(group_queue_data["info_2_tries"])
                    if request_tries <= 4:
                        print(self.warning + "Retrying Group Info Request")
                        message_id = self.client.request_info_of_users(group_queue_data["info_request_2"])
                        request_tries += 1
                        RedisCache(self.config).update_group_queue_json("info_2_tries", request_tries,
                                                                        x.decode('utf-8'), self.bot_id)
                        RedisCache(self.config).update_group_queue_json("info_id_2", message_id,
                                                                        x.decode('utf-8'), self.bot_id)
                        return
                    else:
                        RedisCache(self.config).remove_from_group_queue(x.decode('utf-8'), self.bot_id)
                        print(self.critical + "Group Info Request Failed 5 times. Removing group from group queue.")
                        return

    # Listener for when Peer Info received through Xiphias request.
    def on_xiphias_get_users_response(self, response: Union[UsersResponse, UsersByAliasResponse]):
        PeerInfo(self).xiphias_info_parser(response)

    # ------------------------------------
    #  API - Misc Event Listeners
    # ------------------------------------

    def on_status_message_received(self, response: chatting.IncomingStatusResponse):
        if self.config["general"]["debug"] >= 1:
            print(self.debug + f'Status message from {response.from_jid}: {response.status}.' + Style.RESET_ALL)

        return

    def on_username_uniqueness_received(self, response: UsernameUniquenessResponse):
        if self.config["general"]["debug"] >= 2:
            print(self.debug + f'Is {response.username} a unique username? {response.unique}.' + Style.RESET_ALL)

        if response.username is not None:
            heartbeat_queue = RedisCache(self.config).get_heartbeat_data(self.bot_id)
            if heartbeat_queue:
                trip = time.time() - heartbeat_queue["time"]
                if self.config["general"]["debug"] >= 2:
                    print("Took " + str(trip) + " seconds. Bot Alive")
                heartbeat_queue["received"] = True
                RedisCache(self.config).update_heartbeat_data(heartbeat_queue, self.bot_id)
            else:
                print("Queue was empty!")
        return

    def on_sign_up_ended(self, response: RegisterResponse):
        print(self.info + f'Is Registered as {response.kik_node}.' + Style.RESET_ALL)
        return

    # Listener for when group search is received.
    def on_group_search_response(self, response: GroupSearchResponse):
        print(self.info + f'Search Response: {response.groups}.' + Style.RESET_ALL)

        return

    # Listener for when roster is received.
    def on_roster_received(self, response: FetchRosterResponse):
        if self.config["general"]["debug"] >= 1:
            groups = []
            users = []
            for peer in response.peers:
                if "groups.kik.com" in peer.jid:
                    groups.append(peer.jid)
                else:
                    users.append(peer.jid)

            user_text = '\n'.join([str(us) for us in users])
            group_text = '\n'.join([str(gr) for gr in groups])
            partner_count = len(response.peers)
            print(
                self.info + f'Roster Recieved\nTotal Peers: {str(partner_count)}\n' + Style.BRIGHT + Fore.CYAN + 'Groups:\n' + Style.RESET_ALL + f'{group_text}\n' + Style.BRIGHT + Fore.YELLOW + 'Users:\n' + Style.RESET_ALL + f'{user_text}')

        return

    # Listener for friend attributions
    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        if self.config["general"]["debug"] >= 1:
            print(self.info + f'Friend Request From: {response.referrer_jid}.' + Style.RESET_ALL)
        return

    # ------------------------------------
    #  API - Error Event Listeners
    # ------------------------------------

    def on_connection_failed(self, response: ConnectionFailedResponse):
        print(self.critical + f'Connection failed: {response.message}.' + Style.RESET_ALL)
        return

    def on_login_error(self, login_error: LoginError):
        print(self.critical + f'Login failed: {login_error.error_code}, {login_error.error_messages}.' + Style.RESET_ALL)
        if login_error.is_captcha():
            send_email(self.config, "captcha", self.bot_id)
            heartbeat_queue = RedisCache(self.config).get_heartbeat_data(self.bot_id)
            heartbeat_queue["captcha"] = True
            heartbeat_queue["offline"] = True
            RedisCache(self.config).update_heartbeat_data(heartbeat_queue, self.bot_id)
            sys.exit(1)
        return

    def on_temp_ban_received(self, response: TempBanElement):
        print(self.critical + f'Temporary Ban: {response.ban_title}, {response.ban_message}\nEnds: {response.ban_end_time}.' + Style.RESET_ALL)

        send_email(self.config, "temp_ban", self.bot_id)
        heartbeat_queue = RedisCache(config_data).get_heartbeat_data(self.bot_id)
        heartbeat_queue["captcha"] = False
        heartbeat_queue["offline"] = True
        heartbeat_queue["temp_ban"] = False
        heartbeat_queue["temp_ban_time"] = response.ban_end_time
        RedisCache(config_data).update_heartbeat_data(heartbeat_queue, self.bot_id)

        return

    def on_register_error(self, response: SignUpError):
        print(self.critical + f'Registration Error: {response.message}.' + Style.RESET_ALL)
        return


if __name__ == '__main__':
    main()
    logging.basicConfig(format=KikClient.log_format(), level=logging.INFO)
