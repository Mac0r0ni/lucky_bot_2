import argparse
import binascii
import json
import math
import random
import sys
import time
from lib.bot_config_handler import add, BotConfiguration
from lib.database_handler import Database

parser = argparse.ArgumentParser(description='Process Arguments.')
parser.add_argument("bot_kik_username", help="KIK Username")
parser.add_argument("bot_kik_password", help="KIK Password")
parser.add_argument("bot_id", help="Bot ID# 1-9999")
args = parser.parse_args()

try:
    main_config = open('etc/bot_config.json', 'r')
    config_data = json.load(main_config)
except Exception as e:
    print(repr(e))
    sys.exit(1)


try:
    bot_username = args.bot_kik_username
    bot_password = args.bot_kik_password
    bot_id = int(args.bot_id)
except Exception as e:
    print(repr(e))
    print("Incorrect Account Info Exiting")
    sys.exit(0)


def random_bytes(n):
    a = bytes([random.randint(0, 255) for _ in range(n)])
    b = binascii.hexlify(a)
    return b.decode("ascii")


def random_carrier():
    att = "310016"
    boost = "311870"
    cricket = "310016"
    straight_talk = "310999"
    tmobile = "310160"
    verizon = "310004"
    carrier_list = [att, tmobile, boost, cricket, straight_talk, verizon]
    carrier = random.choice(carrier_list)
    return carrier


def random_number():
    return random.randint(1, 15)


def random_model():
    model_1 = "Samsung Galaxy S20 FE"
    model_2 = "Samsung Galaxy S22"
    model_3 = "Samsung Galaxy A73"
    model_4 = "Samsung Galaxy A23"
    model_5 = "Samsung Galaxy M33"
    model_6 = "Google Pixel 6"
    model_7 = "Google Pixel 5"
    model_8 = "Asus ROG Phone 5s"
    model_list = [model_1, model_2, model_3, model_4, model_5, model_6, model_7, model_8]
    model = random.choice(model_list)
    return model


def random_date(start, end, time_format, prop):
    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))
    ptime = stime + prop * (etime - stime)
    return ptime


def random_device():
    carrier = random_carrier()
    brand = "generic"
    model = random_model()
    android_sdk = "32"
    install_date = math.trunc(
        random_date("1/1/2021 1:10 PM", "10/26/2022 1:10 AM", '%m/%d/%Y %I:%M %p', random.random()))
    logins = random_number()
    registrations = random_number()
    device = [carrier, brand, model, android_sdk, install_date, logins, registrations]
    return device


device_config = random_device()

bot_configuration = BotConfiguration()
bot_configuration.username = bot_username
bot_configuration.password = bot_password
bot_configuration.bot_id = bot_id
bot_configuration.android_id = random_bytes(8)
bot_configuration.device_id = random_bytes(16)
bot_configuration.operator = device_config[0]
bot_configuration.brand = device_config[1]
bot_configuration.model = device_config[2]
bot_configuration.android_sdk = device_config[3]
bot_configuration.install_date = device_config[4]
bot_configuration.logins_since_install = device_config[5]
bot_configuration.registrations_since_install = device_config[6]

try:
    add(bot_configuration)
    Database(config_data).add_new_bot(bot_id, bot_username)
    print("Added Bot " + bot_username + "\n With ID of Bot ID: " + str(bot_id))
except Exception as e:
    print(repr(e))
    print("Incorrect Account Info Exiting")
    sys.exit(0)
