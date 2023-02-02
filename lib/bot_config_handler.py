import json


def read_as_json():
    with open("etc/bot_credentials.json", "r") as json_file:
        data = json.load(json_file)
    return data


def get_bot(botname):
    bot_configurations = []
    data = read_as_json()
    # print(data)
    if botname in data:
        bot_configuration = BotConfiguration()
        bot_configuration.username = botname
        bot_configuration.password = data[botname][0]
        bot_configuration.bot_id = data[botname][1]
        bot_configuration.android_id = data[botname][2]
        bot_configuration.device_id = data[botname][3]
        bot_configuration.operator = data[botname][4]
        bot_configuration.brand = data[botname][5]
        bot_configuration.model = data[botname][6]
        bot_configuration.android_sdk = data[botname][7]
        bot_configuration.install_date = data[botname][8]
        bot_configuration.logins_since_install = data[botname][9]
        bot_configuration.registrations_since_install = data[botname][10]
        bot_configurations.append(bot_configuration)
    return bot_configurations


def add(bot_configuration):
    data = read_as_json()
    data[bot_configuration.username] = [bot_configuration.password, bot_configuration.bot_id,
                                        bot_configuration.android_id,
                                        bot_configuration.device_id, bot_configuration.operator,
                                        bot_configuration.brand,
                                        bot_configuration.model, bot_configuration.android_sdk,
                                        bot_configuration.install_date,
                                        bot_configuration.logins_since_install,
                                        bot_configuration.registrations_since_install]
    with open("etc/bot_credentials.json", "w") as json_file:
        json.dump(data, json_file, indent=4)


class BotConfiguration:
    username = ""
    password = ""
    bot_id = ""
    android_id = ""
    android_sdk = ""
    device_id = ""
    operator = ""
    brand = ""
    model = ""
    install_date = ""
    logins_since_install = ""
    registrations_since_install = ""

