# Python 3 Core Libraries
import json

# Python 3 Third Party Libraries
import os
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageFont

# Python 3 Project Libraries


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


def convert_time(time_in_seconds):
    if time_in_seconds >= 86400:
        btime = (time_in_seconds // 86400)
        if btime == 1:
            b_units = "day"
        else:
            b_units = "days"
    elif 86400 > time_in_seconds >= 3600:
        btime = (time_in_seconds // 3600)
        if btime == 1:
            b_units = "hour"
        else:
            b_units = "hours"
    elif 3600 > time_in_seconds >= 60:
        btime = (time_in_seconds // 60)
        if btime == 1:
            b_units = "minute"
        else:
            b_units = "minutes"
    elif 60 > time_in_seconds > 0:
        btime = time_in_seconds
        if btime == 1:
            b_units = "second"
        else:
            b_units = "seconds"
    else:
        btime = 0
        b_units = "seconds"

    return btime, b_units


def convert_time_precise(secs):
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    result = ("{0} day{1} ".format(days, "s" if days != 1 else "") if days else "") + \
             ("{0} hr{1} ".format(hours, "s" if hours != 1 else "") if hours else "") + \
             ("{0} min{1} ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
             ("{0} sec{1} ".format(seconds, "s" if seconds != 1 else "") if seconds else "")
    return result


# def crop_to_circle(image_uuid, display_name, level, xp, xp_till_next, rank):
#     im = Image.open(config.file_path["rank_img"] + image_uuid + ".jpg").convert('RGBA')
#     bigsize = (im.size[0] * 3, im.size[1] * 3)
#     mask = Image.new('L', bigsize, 0)
#     ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
#     mask = mask.resize(im.size, Image.ANTIALIAS)
#     mask = ImageChops.darker(mask, im.split()[-1])
#     im.putalpha(mask)
#     im.save(config.file_path["rank_img"] + image_uuid + ".png")
#     os.remove(config.file_path["rank_img"] + image_uuid + ".jpg")
#     rank_image(image_uuid, display_name, level, xp, xp_till_next, rank)
#
#
# def slots_image(reel_one, reel_two, reel_three, winnings):
#     command = 'convert -size 500x250 -background transparent -pointsize 65 -gravity center -define pango:justify=center pango:\"' + reel_one + ' ' + reel_two + ' ' + reel_three + ' ' + '\" ' + \
#               config.file_path["slots_img"] + reel_one + '_' + reel_two + '_' + reel_three + '.png'
#     subprocess.check_call([command], shell=True)
#     background = Image.new("RGB", (500, 250), "#202020")
#     foreground = Image.open(config.file_path["slots_img"] + reel_one + '_' + reel_two + '_' + reel_three + '.png')
#     draw = ImageDraw.Draw(background)
#     font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 30)
#     draw.text((60, 160), str(winnings), (255, 255, 255), font=font)
#     background.paste(foreground, (10, 20), foreground)
#     background.save(config.file_path["slots_img"] + reel_one + '_' + reel_two + '_' + reel_three + '.jpg')
#
#     return 1
#
#
# def rank_image(image_uuid, display_name, level, xp, xp_till_next, rank):
#     command = 'convert -size 500x250 -background transparent -fill "#fff" -pointsize 32 -define pango:justify=true pango:\"' + display_name[
#                                                                                                                                :10] + '\" ' + \
#               config.file_path["user_img"] + image_uuid + '_name.png'
#     subprocess.check_call([command], shell=True)
#     background = Image.new("RGB", (500, 250), "#202020")
#     foreground = Image.open(config.file_path["user_img"] + image_uuid + ".png")
#     name_plate = Image.open(config.file_path["user_img"] + image_uuid + "_name.png")
#     foreground.thumbnail([200, 200], Image.ANTIALIAS)
#     draw = ImageDraw.Draw(background)
#     # font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 64)
#     # draw.text((260, 10), display_name[:7], (255, 255, 255), font=font)
#     font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 42)
#     draw.text((325, 100), "Rank " + str(rank), (255, 255, 255), font=font)
#     font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 25)
#     draw.text((325, 160), "Level " + str(level), (255, 255, 255), font=font)
#     font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf", 25)
#     draw.text((325, 200), "XP " + str(xp) + "/" + str(xp_till_next), (255, 255, 255), font=font)
#     fill_length = (500 / xp_till_next) * xp
#     draw.rectangle((0, 230, fill_length, 250), fill=(55, 133, 249))
#     background.paste(foreground, (10, 20), foreground)
#     background.paste(name_plate, (260, 20), name_plate)
#     background.save(config.file_path["user_img"] + image_uuid + ".jpg")


class Help:
    def __init__(self, client):
        self.client = client

    def main(self, chat_message, bot_name):
        s = chat_message.body.lower()

        help_menu = "++ {} Help Menu ++\n".format(str(bot_name).capitalize())
        help_menu += "(Add) to group\n"
        help_menu += "(Welcome) users to group.\n"
        help_menu += "(Lock) a group.\n"
        help_menu += "(Grab) a users @name on join.\n"
        help_menu += "(Roast) have {} roast you.\n"
        help_menu += "(Clear) the chat contents.\n"
        help_menu += "Make the bot (Leave) the chat.\n"
        help_menu += "---------------------------\n"
        help_menu += "Say help (feature) to see that features help page. Example:\nhelp lock"

        help_add = "++ Adding to a group ++\n"
        help_add += "In PM Say: friend\n"
        help_add += "After you are my friend you can add me to a group."

        help_welcome = "++ Welcoming Users to a group ++\n"
        help_welcome += "Description: sends a welcome message when users join.\n"
        help_welcome += "To enable say: {} start welcome\n".format(str(bot_name))
        help_welcome += "To disable say: {} stop welcome\n".format(str(bot_name))
        help_welcome += "To set welcome message:\n {} set welcome message your message\n".format(str(bot_name))
        help_welcome += "To see welcome status: {} welcome status".format(str(bot_name))

        help_lock = "++ Locking a Group ++\n"
        help_lock += "Description: removes any users that joins group.\n"
        help_lock += "To enable say: {} start lock\n".format(str(bot_name))
        help_lock += "To disable say: {} stop lock\n".format(str(bot_name))
        help_lock += "To set lock message:\n {} set lock message your message\n".format(str(bot_name))
        help_lock += "To see lock status: {} lock status".format(str(bot_name))

        help_grab = "++ Name Grab ++\n"
        help_grab += "Description: Grabs users @name on join.\n"
        help_grab += "To enable say: {} start grab\n".format(str(bot_name))
        help_grab += "To disable say: {} stop grab\n".format(str(bot_name))
        help_grab += "To see grab status: {} grab status".format(str(bot_name))

        help_roast = "++ Roast ++\n"
        help_roast += "Description: roasts a user on command.\n"
        help_roast += "To enable say: {} start roast\n".format(str(bot_name))
        help_roast += "To disable say: {} stop roast\n".format(str(bot_name))
        help_roast += "To see roast status: {} roast status\n".format(str(bot_name))
        help_roast += "To have me roast you: {} roast me".format(str(bot_name))

        help_clear = "++ Clear Chat ++\n"
        help_clear += "Description: wipes chat with blank messages.\n"
        help_clear += "To clear chat: {} clear.".format(str(bot_name))

        help_leave = "++ Leave Chat ++\n"
        help_leave += "Description: make {} bot leave chat.".format(str(bot_name))
        help_leave += "To activate say: {} leave".format(str(bot_name))

        if s == "help" or s == "menu":
            Help(self.client).send_message(chat_message, help_menu)
        elif s == "help add":
            Help(self.client).send_message(chat_message, help_add)
        elif s == "help welcome":
            Help(self.client).send_message(chat_message, help_welcome)
        elif s == "help lock":
            Help(self.client).send_message(chat_message, help_lock)
        elif s == "help grab":
            Help(self.client).send_message(chat_message, help_grab)
        elif s == "help roast":
            Help(self.client).send_message(chat_message, help_roast)
        elif s == "help clear":
            Help(self.client).send_message(chat_message, help_clear)
        elif s == "help leave":
            Help(self.client).send_message(chat_message, help_leave)
        else:
            return

    def send_message(self, chat_message, help_message):
        if not chat_message.group_jid:
            self.client.send_chat_message(chat_message.from_jid, help_message)
        else:
            self.client.send_chat_message(chat_message.group_jid, help_message)
