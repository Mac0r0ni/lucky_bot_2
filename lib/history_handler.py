import time

from colorama import Style, Fore

from lib.bot_utility import convert_time_precise, convert_time
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin


class GroupHistory:
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

    def main(self, chat_message, prefix):
        s = chat_message.body.lower()
        if s == prefix + "history top":
            GroupHistory(self).get_user_history_rank(chat_message, "top")
        elif s == prefix + "history bottom":

            GroupHistory(self).get_user_history_rank(chat_message, "bottom")
        elif s == prefix + "history all" or prefix + "history all " in s:
            length = s.split(" ")
            if len(length) == 2:
                GroupHistory(self).get_user_history_rank(chat_message, 1)
            else:
                try:
                    page = int(s.split(prefix + "history all ")[1])
                except TypeError as e:
                    RemoteAdmin(self).send_message(chat_message, f'Give only a number after command\n Example: +history all 2')
                    return
                GroupHistory(self).get_user_history_rank(chat_message, page)

        elif s[:8] == prefix + "history":
            if s[:9] == prefix + "history ":
                user_id = int(s.split(prefix + "history ")[1])
            else:
                group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
                group_members = group_data["group_members"]
                user_id = group_members[chat_message.from_jid]["uid"]

            GroupHistory(self).get_single_user_history(chat_message, user_id)
        else:
            print("no match")

    def get_single_user_history(self, chat_message, uid):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_members = group_data["group_members"]
        group_history = group_data["history"]
        selected_member = False
        if group_members:
            for m in group_members:
                if group_members[m]["uid"] == uid:
                    selected_member = m
            if not selected_member:
                history_response = "User not found."
            else:
                display_name = group_members[selected_member]["display_name"]
                joined_time = round(time.time() - group_members[selected_member]["join_time"])
                messages = group_history[selected_member]["message"]
                images = group_history[selected_member]["image"]
                gifs = group_history[selected_member]["gif"]
                videos = group_history[selected_member]["video"]
                last_active = RedisCache(self.config).get_all_talker_lurkers("talkers", chat_message.group_jid)
                last_lurked = RedisCache(self.config).get_all_talker_lurkers("lurkers", chat_message.group_jid)
                a_time = 0
                l_time = 0
                if last_active:
                    if selected_member in last_active:
                        a_time = convert_time_precise(round(time.time() - last_active[selected_member]))

                if last_lurked:
                    if selected_member in last_lurked:
                        l_time = convert_time_precise(round(time.time() - last_lurked[selected_member]))

                j_time, j_units = convert_time(joined_time)

                history_response = f"++ {display_name[:14]} ++\n"
                history_response += f"First Seen: {str(j_time)} {str(j_units)} ago." + "\n"
                history_response += f"Messages: {str(messages)}" + "\n"
                history_response += f"GIFs: {str(gifs)}" + "\n"
                history_response += f"Images: {str(images)}" + "\n"
                history_response += f"Videos: {str(videos)}" + "\n"
                history_response += f'Last Active: {str(a_time)}{"ago" if a_time != "Not" else ""}.' + "\n"
                history_response += f'Last Seen: {str(l_time)}{"ago" if a_time != "Not" else ""}.' + "\n"

            RemoteAdmin(self).send_message(chat_message, history_response)

    def get_user_history_rank(self, chat_message, place):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_admins = group_data["group_admins"]
        group_members = group_data["group_members"]
        group_history = group_data["history"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", self.bot_id)
        all_admins = {**bot_admins, **group_admins}
        if chat_message.from_jid in all_admins:
            if group_members and group_history:
                ranking_list = {}
                for h in group_history:
                    if h not in group_members:
                        RedisCache(self.config).remove_single_history(h, chat_message.group_jid)
                for m in group_members:
                    if m in group_history:
                        ranking_list[m] = group_history[m]["message"]
                    else:
                        RedisCache(self.config).add_single_history(m, chat_message.group_jid)

                if place == "top":
                    sorted_ranks = {k: v for k, v in
                                    sorted(ranking_list.items(), key=lambda item: item[1], reverse=True)}
                    history_message = f'++++ History {place.capitalize()} ++++ \n'
                    history_message += f'Member'.ljust(20) + f'ID \n'
                    history_message += f'++++++++++++++++++++++++++ \n'

                elif place == "bottom":
                    sorted_ranks = {k: v for k, v in sorted(ranking_list.items(), key=lambda item: item[1])}
                    history_message = f'++++ History {place.capitalize()} ++++ \n'
                    history_message += f'Member'.ljust(20) + f'ID \n'
                    history_message += f'++++++++++++++++++++++++++ \n'

                else:
                    sorted_ranks = {k: v for k, v in
                                    sorted(ranking_list.items(), key=lambda item: item[1], reverse=True)}
                    history_message = f'+++++++ History {str(place)} +++++++ \n'
                    history_message += f'Member'.ljust(20) + f'ID \n'
                    history_message += f'++++++++++++++++++++++++++ \n'

                ranked_list = []
                for r in sorted_ranks:
                    ranked_list.append(r)

                GroupHistory(self).history_output(chat_message, group_members, group_history, ranked_list, place,
                                                          history_message)
        else:
            RemoteAdmin(self).send_message(chat_message, f'Only Admins can use {chat_message.body}')

    def history_output(self, chat_message, group_members, history_data, sorted_ranks, place, history_message):
        if place == "top":
            sorted_ranks = sorted_ranks[:10]
        elif place == "bottom":
            sorted_ranks = sorted_ranks[:10]
        else:
            total_pages = round(((round(len(sorted_ranks) / 10)) * 10) / 15)
            ranking = place * 15
            sorted_ranks = sorted_ranks[ranking - 15:ranking]

        for x in sorted_ranks:
            history_message += str(group_members[x]["display_name"])[:10] + "      " + str(
                group_members[x]["uid"]) + "\n"
            history_message += "Messages: " + str(history_data[x]["message"]) + "\n" + "GIFs: " + str(history_data[x]["gif"]) + "\n" + "Images: " \
                               + str(history_data[x]["image"]) + "\n" + "Videos: " \
                               + str(history_data[x]["video"]) + "\n"
            history_message += str("                           \n")

        if isinstance(place, int):
            if place <= total_pages:
                history_message += f'+++++++ Page {str(place)}/{str(total_pages)} +++++++'
        else:
            history_message += f'++++++++++++++++++++++++++ \n'
        RemoteAdmin(self).send_message(chat_message, history_message)