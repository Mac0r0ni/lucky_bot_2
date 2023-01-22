import random

from colorama import Style, Fore

from lib.feature_status_handler import FeatureStatus
from lib.redis_handler import RedisCache
from lib.remote_admin_handler import RemoteAdmin


class ChanceGames:
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

    def main(self, chat_message, prefix, name):
        group_data = RedisCache(self.config).get_all_group_data(chat_message.group_jid)
        group_messages = group_data["group_messages"]
        group_settings = group_data["group_settings"]
        group_admins = group_data["group_admins"]

        s = chat_message.body.lower()
        if prefix + "8ball " in s:
            ChanceGames(self).magicball(chat_message, name)

        elif s == prefix + "roll" or "🎲" in s:

            if "🎲" in s:
                num_dice = s.count("🎲")
            else:
                num_dice = 1
            if num_dice > 5:
                RemoteAdmin(self).send_message(chat_message, "I can only roll 5 dice.")
                return
            ChanceGames(self).dice(chat_message, num_dice, int(group_settings["dice_default"]),
                                          name)
        elif prefix + "roll d" in s:
            sides = s.split(prefix + "roll d")[1]
            if sides != "":
                if int(sides) > 10000 or int(sides) <= 1:
                    RemoteAdmin(self).send_message(chat_message,
                                                          name + ", You must specify a number. Between 2 and 10000")
                else:
                    ChanceGames(self).dice(chat_message, 1, int(sides), name)
            else:
                RemoteAdmin(self).send_message(chat_message,
                                                      name + ", You must specify a number. Between 2 and 10000")

        elif prefix + "roll set " in s:
            sides = s.split(prefix + "roll set ")[1]
            if sides != "":
                if int(sides) > 10000 or int(sides) <= 1:
                    RemoteAdmin(self).send_message(chat_message,
                                                          name + ", You must specify a number. Between 2 and 10000")
                else:
                    FeatureStatus(self).set_feature_setting(chat_message, "dice_default", int(sides))
            else:
                RemoteAdmin(self).send_message(chat_message,
                                                      name + ", You must specify a number. Between 2 and 10000")

        elif s == prefix + "roll status":
            if group_settings:
                RemoteAdmin(self).send_message(chat_message,
                                                      "🎲  Dice Default Sides: " + str(group_settings["dice_default"]))

        else:
            RemoteAdmin(self).send_message(chat_message, name + ", Invalid option.")

    def dice(self, chat_message, number_dice, number_sides, name):
        roll_message = "🎲   "
        for i in range(number_dice):
            get_roll = self.roll(number_sides)
            roll_message += "[ " + str(get_roll) + " ]   "
        RemoteAdmin(self).send_message(chat_message, roll_message)

    def roll(self, sides):
        return random.randint(1, sides)

    def magicball(self, chat_message, name):
        mb = {
            "1": "I am totally sure of that one.",
            "2": "Does a bear shit in the woods?",
            "3": "Absofuckinglutley",
            "4": "In the words of SteveO - Yea DUUUUDE",
            "5": "Does the Tin Man have a metal cock?",
            "6": "Yes, but it would be better if you were drunk.",
            "7": "Maybe yes, maybe no...",
            "8": "Yea sure, if that is what you want.",
            "9": "Go away, I'm busy.",
            "10": "Does a duck with a boner drag weeds?",
            "11": "Im too high for your nonsense...",
            "12": "Ask later, I don't feel like answering you.",
            "13": "You can't handle the correct answer right now.",
            "14": "Why are you asking me? I am not even real??",
            "15": "Come back when you have thought about it more...",
            "16": "Don't count on it dingus.",
            "17": "...Dude no... Just no... Why would you even want that?",
            "18": "Nah.",
            "19": "No fucking way...",
            "20": "You have a better chance of being eaten by a shark."
        }
        wisdom = random.choice(list(mb))
        RemoteAdmin(self).send_message(chat_message, name + ", 🎱 " + str(mb[wisdom]))