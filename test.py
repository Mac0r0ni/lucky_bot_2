import json

from lib.database_handler import Database
from lib.redis_handler import RedisCache

main_config = open('etc/bot_config.json', 'r')
config_data = json.load(main_config)

result = Database(config_data).get_all_groups_jid()

for x in result:

    group_data = RedisCache(config_data).get_all_group_data(x)
    group_settings = group_data["group_settings"]
    if group_settings:
        if "sfw_status" not in group_settings:
            group_settings["sfw_status"] = 0
            try:
                Database(config_data).update_group_data("json", "group_settings", group_settings, x)
            except Exception as e:
                print(repr(e))
                print("Group: " + str(x) + "Failed")
                print(group_settings)
                break
            print("Updated Group: " + str(x))
        else:
            continue
    else:
        continue