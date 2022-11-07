import json

from lib.database_handler import Database

main_config = open('etc/bot_config.json', 'r')
config_data = json.load(main_config)

result = Database(config_data).get_all_substitution("1100257133458_g")
print(result)