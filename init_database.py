import json

from lib.database_handler import Database


main_config = open('etc/bot_config.json', 'r')
config_data = json.load(main_config)

print("Creating Tables")
Database(config_data).remove_bot_database_tables()
Database(config_data).initalize_bot_database()
print("Complete")