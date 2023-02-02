import json
import os
import shutil

import mysql.connector as mysql
from colorama import Fore, Style

from lib.bot_utility import is_json
from lib.redis_handler import RedisCache


class Database:
    def __init__(self, config_data):
        self.connection = mysql.connect(
            host=config_data["mysql"]["hostname"],
            port=config_data["mysql"]["port"],
            user=config_data["mysql"]["username"],
            password=config_data["mysql"]["password"],
            database=config_data["mysql"]["database"],
            auth_plugin='mysql_native_password'
        )
        self.config = config_data
        self.cursor = self.connection.cursor()
        self.group_column_list = ["group_hash", "group_name", "group_settings",
                                  "group_messages", "group_owner", "group_admins", "group_members", "user_triggers",
                                  "admin_triggers", "censor_words", "group_id", "bot_id"]
        self.bot_column_list = ["bot_name", "bot_settings", "bot_whitelist_groups", "bot_blacklist_groups",
                                "bot_admins"]
        self.debug = f'[' + Style.BRIGHT + Fore.CYAN + '^' + Style.RESET_ALL + '] '
        self.info = f'[' + Style.BRIGHT + Fore.CYAN + '+' + Style.RESET_ALL + '] '
        self.warning = f'[' + Style.BRIGHT + Fore.YELLOW + '!' + Style.RESET_ALL + '] '
        self.critical = f'[' + Style.BRIGHT + Fore.RED + 'X' + Style.RESET_ALL + '] '

    def initalize_bot_database(self):
        group_table_query = "CREATE TABLE group_data (group_id int(11) NOT NULL COMMENT 'Auto Incremented Group ID', group_jid varchar(16) NOT NULL COMMENT 'KIK Group JID', group_hash varchar(40) NOT NULL COMMENT 'KIK Group Hash', group_name varchar(100) NOT NULL COMMENT 'KIK Group Name', group_settings text NOT NULL COMMENT 'Bot Function Settings', group_messages text NOT NULL COMMENT 'Custom Bot Messages', group_owner text NOT NULL COMMENT 'Group Owner', group_admins text NOT NULL COMMENT 'Group Admins', group_members text NOT NULL COMMENT 'Group Members', user_triggers mediumtext NOT NULL COMMENT 'User Triggers', admin_triggers mediumtext NOT NULL COMMENT 'Admin Triggers', censor_words mediumtext NOT NULL COMMENT 'Censor Words', bot_id int(4) NOT NULL COMMENT 'ID Number of Bot - 1-9999')"
        group_alter_query = "ALTER TABLE group_data ADD PRIMARY KEY (group_id), ADD UNIQUE KEY group_jid (group_jid), ADD KEY group_jid_2 (group_jid), ADD KEY group_hash (group_hash), ADD KEY bot_id (bot_id)"
        group_modify_query = "ALTER TABLE group_data MODIFY group_id int(11) NOT NULL AUTO_INCREMENT COMMENT 'Auto Incremented Group ID'"
        bot_table_query = "CREATE TABLE `bot_data` (`bot_id` int(4) NOT NULL COMMENT 'Bot ID # 1-9999', `bot_name` varchar(75) NOT NULL COMMENT 'Bot Name', `bot_settings` text NOT NULL DEFAULT '{}' COMMENT 'Bot Settings - JSON Format', `bot_whitelist_groups` text NOT NULL DEFAULT '[]' COMMENT 'Whitelisted Groups - Python List Format', `bot_blacklist_groups` text NOT NULL DEFAULT '[]' COMMENT 'Blacklisted Groups - Python List Format', `bot_admins` text NOT NULL DEFAULT '[]' COMMENT 'Bot Admin JID - Python List Format')"
        bot_alter_query = "ALTER TABLE `bot_data` ADD PRIMARY KEY (`bot_id`), ADD UNIQUE KEY `bot_id` (`bot_id`)"
        self.cursor.execute(group_table_query)
        self.cursor.execute(group_alter_query)
        self.cursor.execute(group_modify_query)
        self.cursor.execute(bot_table_query)
        self.cursor.execute(bot_alter_query)
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def remove_bot_database_tables(self):
        remove_group_table = "DROP TABLE IF EXISTS group_data"
        remove_bot_table = "DROP TABLE IF EXISTS bot_data "
        self.cursor.execute(remove_group_table)
        self.cursor.execute(remove_bot_table)
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    # ------------------------------------
    #  Database Group Data Functions
    # ------------------------------------

    def add_group_to_database(self, group_jid, group_hash, group_name, group_settings, group_messages, group_owner,
                              group_admins, group_members, user_triggers, admin_triggers, censor_words, bot_id):
        # add a new group to database
        query = f'INSERT INTO group_data (group_jid, group_hash, group_name, group_settings, group_messages, group_owner, group_admins, group_members, user_triggers, admin_triggers, censor_words, bot_id) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        self.cursor.execute(query, (
            group_jid.split("@")[0], group_hash, group_name, json.dumps(group_settings), json.dumps(group_messages),
            json.dumps(group_owner),
            json.dumps(group_admins), json.dumps(group_members), json.dumps(user_triggers), json.dumps(admin_triggers),
            json.dumps(censor_words), bot_id))
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def update_group_database(self, group_jid, group_name, group_owner, group_admins, group_members):
        # update group name and users for existing group in database
        query = f'UPDATE group_data SET group_name = %s, group_owner = %s, group_admins = %s, group_members = %s WHERE group_jid = %s'
        self.cursor.execute(query, (
            group_name, json.dumps(group_owner), json.dumps(group_admins), json.dumps(group_members),
            group_jid.split("@")[0]))
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        Database(self.config).load_single_group_cache(group_jid)

    def check_for_group(self, group_jid):
        # check if group exists in database
        query = f'SELECT group_jid from group_data WHERE group_jid = %s'
        self.cursor.execute(query, (group_jid.split("@")[0],))
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            return True
        else:
            return False

    def get_all_groups_jid(self):
        # get all the groups jids from the database in list
        query = 'SELECT group_jid FROM group_data'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        jid_list = [da[0] for da in data]
        self.cursor.close()
        self.connection.close()
        return jid_list

    def get_bot_group_count(self, bot_id):
        query = f'SELECT COUNT(group_jid) AS total FROM group_data WHERE bot_id = {bot_id}'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            return data[0][0]
        else:
            return 0

    def get_group_data_by_hash(self, type, key, group_hash):
        # get a single group item by group hash
        query = f'SELECT {key} FROM group_data WHERE group_hash = %s'
        self.cursor.execute(query, (group_hash.lower(),))
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            if type == "json" or type == "list":
                return json.loads(data[0][0])
            elif type == "str":
                return str(data[0][0])
            elif type == "int":
                return int(data[0][0])
            else:
                return data[0][0]
        else:
            return False

    def get_group_data_by_gjid(self, type, key, group_jid):
        # get a single group item by group hash
        query = f'SELECT {key} FROM group_data WHERE group_jid = %s'
        self.cursor.execute(query, (group_jid.split("@")[0],))
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            if type == "json" or type == "list":
                return json.loads(data[0][0])
            elif type == "str":
                return str(data[0][0])
            elif type == "int":
                return int(data[0][0])
            else:
                return data[0][0]
        else:
            return False

    def update_group_data(self, type, key, value, group_jid):
        # update a single group item by group jid
        query = "UPDATE group_data SET " + key + " = %s  WHERE group_jid = %s"

        if type == "json" or "list":
            self.cursor.execute(query, (json.dumps(value), group_jid.split("@")[0]))
        else:
            self.cursor.execute(query, (value, group_jid.split("@")[0]))

        RedisCache(self.config).update_group_data(key, value, group_jid)

        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def remove_group(self, group_jid):
        # delete group from database
        query = f'DELETE FROM group_data WHERE `group_jid` = %s'
        self.cursor.execute(query, (group_jid.split("@")[0],))
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def get_groups_list(self):
        groups = Database(self.config).get_all_groups_jid()
        groups_list = "Groups I am in: \n"
        count = 0
        for group in groups:
            count += 1
            group_hash = Database(self.config).get_group_data_by_gjid("single", "group_hash", group)
            group_name = Database(self.config).get_group_data_by_gjid("single", "group_name", group)
            groups_list += str(count) + " \n"
            groups_list += str(group_hash) + "\n"
            groups_list += str(group_name) + "\n"

        return groups_list

    # ------------------------------------
    #  Group Feature Change Functions
    # ------------------------------------

    # not right need to get the data from redis, change the json.
    def change_feature_status(self, status, feature, group_jid, peer_jid, bot_id):
        group_jid = group_jid.split('@')[0]
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        group_settings = group_data["group_settings"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        all_admins = {**bot_admins, **group_admins}
        if peer_jid in all_admins:
            if group_settings[feature] != status:
                group_settings[feature] = status
                query = f'UPDATE group_data SET group_settings = %s WHERE group_jid = %s'
                self.cursor.execute(query, (json.dumps(group_settings), group_jid))
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
                RedisCache(self.config).update_group_data("group_settings", group_settings, group_jid)
                return 1
            else:
                return 2
        else:
            return 3

    def change_feature_message(self, setting, value, group_jid, peer_jid, bot_id):
        group_jid = group_jid.split('@')[0]
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        all_admins = {**bot_admins, **group_admins}
        self.cursor = self.connection.cursor()
        query = f'SELECT group_messages FROM group_data WHERE group_jid = %s'
        self.cursor.execute(query, (group_jid,))
        data = self.cursor.fetchall()
        if data:
            group_messages = json.loads(data[0][0])
        else:
            group_messages = False
        if peer_jid in all_admins and group_messages:
            if setting not in group_messages:
                return 2
            group_messages[setting] = value
            query = f'UPDATE group_data SET group_messages = %s WHERE group_jid = %s'
            self.cursor.execute(query, (json.dumps(group_messages), group_jid))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("group_messages", group_messages, group_jid)
            return 1
        else:
            return 2

    def change_feature_setting(self, setting, value, peer_jid, group_jid, bot_id):
        group_jid = group_jid.split('@')[0]
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        all_admins = {**bot_admins, **group_admins}

        if peer_jid in all_admins:
            group_settings = group_data["group_settings"]
            group_settings[setting] = value
            query = "UPDATE group_data SET group_settings = %s WHERE group_jid = %s"
            self.cursor.execute(query, (json.dumps(group_settings), group_jid))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("group_settings", group_settings, group_jid)
            return 1
        else:
            return 2

    # ------------------------------------
    #  Database Bot Data Functions
    # ------------------------------------

    def add_new_bot(self, bot_id, bot_name):
        query = f'INSERT INTO bot_data (bot_id, bot_name) VALUES ({bot_id}, \'{bot_name}\')'
        self.cursor.execute(query)
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def update_bot_data(self, type, key, value, bot_id):
        if type == "json" or "list":
            query = f'UPDATE bot_data SET {key} = \'{json.dumps(value)}\' WHERE bot_id = {bot_id}'
        else:
            query = f'UPDATE bot_data SET {key} = {value} WHERE bot_id = {bot_id}'
        self.cursor.execute(query)
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def get_bot_data(self, type, key, bot_id):
        query = f'SELECT {key} FROM bot_data WHERE bot_id = {bot_id}'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            if type == "json" or type == "list":
                return json.loads(data[0][0], strict=False)
            elif type == "str":
                return str(data[0][0])
            elif type == "int":
                return int(data[0][0])
            else:
                return data[0][0]
        else:
            return False

    def get_all_bot_data(self, bot_id):
        query = f'SELECT * from bot_data WHERE bot_id = {bot_id}'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            return data[0][0]
        else:
            return False

    # ------------------------------------
    #  Database -> Cache Functions
    # ------------------------------------

    def load_all_bot_groups_to_cache(self, bot_id):
        query = f'SELECT * FROM group_data WHERE bot_id = %s'
        self.cursor.execute(query, (bot_id,))
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        if data:
            RedisCache(self.config).add_to_cache(data, self.group_column_list)

    def load_single_group_cache(self, group_jid):
        group_jid = group_jid.split('@')[0]
        # get data from MySQL for a single group by JID
        query = f'SELECT * FROM group_data WHERE group_jid = \'{group_jid}\''
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        # Send that data and the group column list to the redis add with pipe
        RedisCache(self.config).add_to_cache(data, self.group_column_list)

    def load_bot_data_to_cache(self, bot_id):
        query = f'SELECT * FROM bot_data WHERE bot_id = {bot_id}'
        self.cursor.execute(query)
        data = self.cursor.fetchall()
        self.cursor.close()
        self.connection.close()
        RedisCache(self.config).add_to_cache(data, self.bot_column_list)

    # -----------------------------------
    #  Substitutions Database Functions
    # -----------------------------------

    def set_substitution(self, sub_type, sub, group_jid, peer_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        user_triggers = group_data["user_triggers"]
        admin_triggers = group_data["admin_triggers"]
        all_admins = {**bot_admins, **group_admins}
        if sub_type == "admin_triggers":
            if peer_jid in all_admins:
                if user_triggers:
                    if sub[0] in user_triggers:
                        Database(self.config).delete_substitution("user_triggers", sub, group_jid, peer_jid, bot_id)
                if str(sub[0]) in admin_triggers:
                    if len(admin_triggers[str(sub[0]).lower()]) >= 2:
                        return 4
                    else:
                        admin_triggers[str(sub[0]).lower()] = {0: sub[1]}
                else:
                    admin_triggers[str(sub[0]).lower()] = {0: sub[1]}

                query = "UPDATE group_data SET admin_triggers = %s WHERE group_jid = %s"
                self.cursor.execute(query, (json.dumps(admin_triggers), group_jid.split('@')[0]))
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
                RedisCache(self.config).update_group_data("admin_triggers", admin_triggers, group_jid)
                RedisCache(self.config).update_group_data("user_triggers", user_triggers, group_jid)
                return 1
            else:
                return 2
        else:
            if str(sub[0]) in user_triggers:
                if len(user_triggers[str(sub[0]).lower()]) >= 2:
                    return 4
                else:
                    user_triggers[str(sub[0]).lower()] = {0: sub[1]}
            else:
                user_triggers[str(sub[0]).lower()] = {0: sub[1]}
            query = "UPDATE group_data SET user_triggers = %s WHERE group_jid = %s"
            self.cursor.execute(query, (json.dumps(user_triggers), group_jid.split('@')[0]))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("user_triggers", user_triggers, group_jid)
            return 3

    def update_substitution(self, sub_type, sub, group_jid, peer_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        user_triggers = group_data["user_triggers"]
        admin_triggers = group_data["admin_triggers"]
        all_admins = {**bot_admins, **group_admins}
        sub_max = list(range(40))
        if sub_type == "admin_triggers":
            if peer_jid in all_admins:
                if admin_triggers.get(str(sub[0]).lower()):
                    if len(admin_triggers[str(sub[0]).lower()]) >= len(sub_max):
                        return 5
                    else:
                        for x in admin_triggers[str(sub[0]).lower()]:
                            sub_max.remove(int(x))
                        admin_triggers[str(sub[0]).lower()][sub_max[0]] = sub[1]
                else:
                    admin_triggers[str(sub[0]).lower()] = {sub_max[0]: sub[1]}
                query = "UPDATE group_data SET admin_triggers = %s WHERE group_jid = %s"
                self.cursor.execute(query, (json.dumps(admin_triggers), group_jid.split('@')[0]))
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
                RedisCache(self.config).update_group_data("admin_triggers", admin_triggers, group_jid)
                return 1
            else:
                return 2
        else:
            if user_triggers.get(str(sub[0]).lower()):
                if len(user_triggers[str(sub[0]).lower()]) >= len(sub_max):
                    return 5
                else:
                    for x in user_triggers[str(sub[0]).lower()]:
                        sub_max.remove(int(x))
                    user_triggers[str(sub[0]).lower()][sub_max[0]] = sub[1]
            else:
                user_triggers[str(sub[0]).lower()] = {sub_max[0]: sub[1]}
            query = "UPDATE group_data SET user_triggers = %s WHERE group_jid = %s"
            self.cursor.execute(query, (json.dumps(user_triggers), group_jid.split('@')[0]))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("user_triggers", user_triggers, group_jid)
            return 3

    def delete_sub_substitution(self, sub_type, sub, number, group_jid, peer_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        user_triggers = group_data["user_triggers"]
        admin_triggers = group_data["admin_triggers"]
        all_admins = {**bot_admins, **group_admins}
        if sub_type == "admin_triggers":

            if peer_jid in all_admins:
                if admin_triggers[sub][number][-3:] == "png" or admin_triggers[sub][number][-3:] == "jpg":
                    if os.path.exists(admin_triggers[sub][number]):
                        os.remove(admin_triggers[sub][number])
                elif admin_triggers[sub][number][-3:] == "mp4":
                    if os.path.exists(admin_triggers[sub][number]):
                        os.remove(admin_triggers[sub][number])
                        os.remove(admin_triggers[sub][number].replace("mp4", "jpg"))
                elif admin_triggers[sub][number][-4:] == "json":
                    if os.path.exists(admin_triggers[sub][number]):
                        os.remove(admin_triggers[sub][number])
                del admin_triggers[sub][number]
                query = "UPDATE group_data SET admin_triggers = %s WHERE group_jid = %s"
                self.cursor.execute(query, (json.dumps(admin_triggers), group_jid.split('@')[0]))
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
                RedisCache(self.config).update_group_data("admin_triggers", admin_triggers, group_jid)
                return 1
            else:
                return 2
        else:

            if user_triggers[sub][number][-3:] == "png" or user_triggers[sub][number][-3:] == "jpg":
                if os.path.exists(user_triggers[sub][number]):
                    os.remove(user_triggers[sub][number])
            elif user_triggers[sub][number][-3:] == "mp4":
                if os.path.exists(user_triggers[sub][number]):
                    os.remove(user_triggers[sub][number])
                    os.remove(user_triggers[sub][number].replace("mp4", "jpg"))
            elif user_triggers[sub][number][-4:] == "json":
                if os.path.exists(user_triggers[sub][number]):
                    os.remove(user_triggers[sub][number])
            del user_triggers[sub][number]
            query = "UPDATE group_data SET user_triggers = %s WHERE group_jid = %s"
            self.cursor.execute(query, (json.dumps(user_triggers), group_jid.split('@')[0]))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("user_triggers", user_triggers, group_jid)
            return 4

    def delete_substitution(self, sub_type, sub, group_jid, peer_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        user_triggers = group_data["user_triggers"]
        admin_triggers = group_data["admin_triggers"]
        all_admins = {**bot_admins, **group_admins}
        if sub_type == "admin_triggers":

            if peer_jid in all_admins:

                for x in admin_triggers[sub]:
                    if admin_triggers[sub][x][-3:] == "png" or admin_triggers[sub][x][-3:] == "jpg":
                        if os.path.exists(admin_triggers[sub][x]):
                            os.remove(admin_triggers[sub][x])
                    elif admin_triggers[sub][x][-3:] == "mp4":
                        if os.path.exists(admin_triggers[sub][x]):
                            os.remove(admin_triggers[sub][x])
                        if os.path.exists(admin_triggers[sub][x].replace("mp4", "jpg")):
                            os.remove(admin_triggers[sub][x].replace("mp4", "jpg"))
                    elif admin_triggers[sub][x][-4:] == "json":
                        if os.path.exists(admin_triggers[sub][x]):
                            os.remove(admin_triggers[sub][x])
                del admin_triggers[sub]
                query = "UPDATE group_data SET admin_triggers = %s WHERE group_jid = %s"
                self.cursor.execute(query, (json.dumps(admin_triggers), group_jid.split('@')[0]))
                self.connection.commit()
                self.cursor.close()
                self.connection.close()
                RedisCache(self.config).update_group_data("admin_triggers", admin_triggers, group_jid)
                return 1
            else:
                return 2
        else:

            for x in user_triggers[sub]:
                if user_triggers[sub][x][-3:] == "png" or user_triggers[sub][x][-3:] == "jpg":
                    if os.path.exists(user_triggers[sub][x]):
                        os.remove(user_triggers[sub][x])
                    elif user_triggers[sub][x][-3:] == "mp4":
                        if os.path.exists(user_triggers[sub][x]):
                            os.remove(user_triggers[sub][x])
                        if os.path.exists(user_triggers[sub][x].replace("mp4", "jpg")):
                            os.remove(user_triggers[sub][x].replace("mp4", "jpg"))
                    elif user_triggers[sub][x][-4:] == "json":
                        if os.path.exists(user_triggers[sub][x]):
                            os.remove(user_triggers[sub][x])
            del user_triggers[sub]
            query = "UPDATE group_data SET user_triggers = %s WHERE group_jid = %s"
            self.cursor.execute(query, (json.dumps(user_triggers), group_jid.split('@')[0]))
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("user_triggers", user_triggers, group_jid)
            return 4

    def delete_all_substitutions(self, group_jid, peer_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        user_triggers = group_data["user_triggers"]
        admin_triggers = group_data["admin_triggers"]
        all_admins = {**bot_admins, **group_admins}
        current_dir = os.getcwd() + "/"

        if peer_jid in all_admins:
            query = "UPDATE group_data SET admin_triggers = %s, user_triggers = %s WHERE group_jid = %s"
            user = {}
            admin = {}
            self.cursor.execute(query, (json.dumps(user), json.dumps(admin), group_jid.split('@')[0]))
            if os.path.exists(current_dir + self.config["paths"]["trigger_media"] + group_jid):
                shutil.rmtree(current_dir + self.config["paths"]["trigger_media"] + group_jid)
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
            RedisCache(self.config).update_group_data("admin_triggers", admin, group_jid)
            RedisCache(self.config).update_group_data("user_triggers", user, group_jid)
            return 1
        else:
            return 2

    def get_all_substitution(self, group_jid):
        self.cursor.execute("SELECT admin_triggers, user_triggers FROM group_data WHERE group_jid = %s",
                            (group_jid.split('@')[0],))
        data = self.cursor.fetchall()
        admin_triggers = json.loads(data[0][0])
        user_triggers = json.loads(data[0][1])
        merged_triggers = {**user_triggers, **admin_triggers}
        self.cursor.close()
        self.connection.close()
        return merged_triggers

    def get_admin_substitution(self, group_jid):
        self.cursor.execute("SELECT admin_triggers FROM group_data WHERE group_jid = %s",
                            (group_jid.split('@')[0],))
        data = self.cursor.fetchall()
        admin_subs = json.loads(data[0][0])
        self.cursor.close()
        self.connection.close()
        return admin_subs

    def get_user_substitution(self, group_jid):
        self.cursor.execute("SELECT user_triggers FROM group_data WHERE group_jid = %s",
                            (group_jid.split('@')[0],))
        data = self.cursor.fetchall()
        user_subs = json.loads(data[0][0])
        self.cursor.close()
        self.connection.close()
        return user_subs

    # ------------------------------------
    #  Group Backup/Restore/Transfer Database
    # ------------------------------------

    def backup_all_groups_database(self):
        groups = Database(self.config).get_all_groups_jid()
        count = 0
        for gr in groups:
            count += 1
            query = "SELECT * from group_data WHERE group_jid = %s"
            self.cursor.execute(query, (gr,))
            row_headers = [x[0] for x in self.cursor.description]  # this will extract row headers
            rv = self.cursor.fetchall()
            json_data = []
            for result in rv:
                json_data.append(dict(zip(row_headers, result)))
            if not os.path.exists(self.config["paths"]["backup"] + gr + "@groups.kik.com"):
                os.mkdir(self.config["paths"]["backup"] + gr + "@groups.kik.com")
            with open(self.config["paths"]["backup"] + gr + "@groups.kik.com/database.json", 'w+') as backup:
                json.dump(json_data, backup, indent=4)
                backup.close()
            if os.path.exists(self.config["paths"]["trigger_media"] + gr + "@groups.kik.com"):
                source = self.config["paths"]["trigger_media"] + gr + "@groups.kik.com"
                if os.path.exists(self.config["paths"]["backup"] + gr + "@groups.kik.com/trigger"):
                    shutil.rmtree(self.config["paths"]["backup"] + gr + "@groups.kik.com/trigger")

                dest = self.config["paths"]["backup"] + gr + "@groups.kik.com/trigger"
                shutil.copytree(source, dest)
            if os.path.exists(self.config["paths"]["message_media"] + gr + "@groups.kik.com"):
                source = self.config["paths"]["message_media"] + gr + "@groups.kik.com"
                if os.path.exists(self.config["paths"]["backup"] + gr + "@groups.kik.com/message"):
                    shutil.rmtree(self.config["paths"]["backup"] + gr + "@groups.kik.com/message")

                dest = self.config["paths"]["backup"] + gr + "@groups.kik.com/message"
                shutil.copytree(source, dest)

        self.cursor.close()
        self.connection.close()
        return count

    def backup_group_database(self, peer_jid, group_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        all_admins = {**bot_admins, **group_admins}
        if peer_jid in all_admins:
            query = "SELECT * from group_data WHERE group_jid = %s"
            self.cursor.execute(query, (group_jid.split('@')[0],))
            row_headers = [x[0] for x in self.cursor.description]  # this will extract row headers
            rv = self.cursor.fetchall()
            json_data = []
            for result in rv:
                json_data.append(dict(zip(row_headers, result)))
            if not os.path.exists(self.config["paths"]["backup"] + group_jid):
                os.mkdir(self.config["paths"]["backup"] + group_jid)
            with open(self.config["paths"]["backup"] + group_jid + "/database.json", 'w+') as backup:
                json.dump(json_data, backup, indent=4)
                backup.close()
            if os.path.exists(self.config["paths"]["trigger_media"] + group_jid):
                source = self.config["paths"]["trigger_media"] + group_jid
                if os.path.exists(self.config["paths"]["backup"] + group_jid + "/trigger"):
                    shutil.rmtree(self.config["paths"]["backup"] + group_jid + "/trigger")

                dest = self.config["paths"]["backup"] + group_jid + "/trigger"
                shutil.copytree(source, dest)
            if os.path.exists(self.config["paths"]["message_media"] + group_jid):
                source = self.config["paths"]["message_media"] + group_jid
                if os.path.exists(self.config["paths"]["backup"] + group_jid + "/message"):
                    shutil.rmtree(self.config["paths"]["backup"] + group_jid + "/message")

                dest = self.config["paths"]["backup"] + group_jid + "/message"
                shutil.copytree(source, dest)
            return 1
        else:
            return 2

    def transfer_group_database(self, source_hash, destination_hash, peer_jid, message_source, bot_id):
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        source_group_jid = Database(self.config).get_group_data_by_hash("str", "group_jid", source_hash)
        if not source_group_jid:
            return 5, str(source_group_jid) + "@groups.kik.com"
        destination_group_jid = Database(self.config).get_group_data_by_hash("str", "group_jid", destination_hash)
        if not destination_group_jid:
            return 6, str(destination_group_jid) + "@groups.kik.com"

        source_ajid = "none"
        destination_ajid = "none"
        new_peer_jid = "none"

        source_data = RedisCache(self.config).get_all_group_data(source_group_jid)
        source_admins = source_data["group_admins"]
        source_members = source_data["group_members"]
        destination_data = RedisCache(self.config).get_all_group_data(destination_group_jid)
        destination_admins = destination_data["group_admins"]
        destination_members = destination_data["group_members"]

        if message_source == "pm" and peer_jid not in bot_admins:
            if source_members:
                for sm in source_members:
                    if source_members[sm]["jid"] == peer_jid:
                        source_ajid = sm
                        break
            if destination_members:
                for dm in destination_members:
                    if destination_members[dm]["jid"] == peer_jid:
                        destination_ajid = dm
                        break

        elif message_source == "gm" and peer_jid not in bot_admins:
            if source_members:
                for sm in source_members:
                    if sm == peer_jid:
                        source_ajid = sm
                        new_peer_jid = source_members[sm]["jid"]
                        break
            if destination_members:
                if new_peer_jid == "Unknown" or new_peer_jid == "none":
                    return 8, str(destination_group_jid) + "@groups.kik.com"
                for dm in destination_members:
                    if destination_members[dm]["jid"] == new_peer_jid:
                        destination_ajid = dm
                        break

        elif message_source == "gm" or message_source == "pm" and peer_jid in bot_admins:
            source_ajid = peer_jid
            destination_ajid = peer_jid

        source_all_admins = {**bot_admins, **source_admins}
        destination_all_admins = {**bot_admins, **destination_admins}

        if source_ajid == "none":
            return 7, str(destination_group_jid) + "@groups.kik.com"
        elif destination_ajid == "none":
            return 8, str(destination_group_jid) + "@groups.kik.com"
        elif source_ajid not in source_all_admins:
            return 2, str(destination_group_jid) + "@groups.kik.com"
        elif destination_ajid not in destination_all_admins:
            return 3, str(destination_group_jid) + "@groups.kik.com"
        else:
            Database(self.config).backup_group_database(source_ajid, source_group_jid, bot_id)
            self.cursor.execute(
                "SELECT group_settings, group_name, group_owner, group_admins, group_members FROM group_data WHERE group_jid = %s",
                (str(destination_group_jid),))
            dest_group_data = self.cursor.fetchall()
            owner = {"none": "Unknown"}
            admins = {"none": "Unknown"}
            members = {"none": "Unknown"}
            group_settings_dst = {}
            if is_json(dest_group_data[0][0]):
                group_settings_dst = json.loads(dest_group_data[0][0])
            if is_json(dest_group_data[0][2]):
                owner = json.loads(dest_group_data[0][2])
            if is_json(dest_group_data[0][3]):
                admins = json.loads(dest_group_data[0][3])
            if is_json(dest_group_data[0][4]):
                members = json.loads(dest_group_data[0][4])

            if admins == {"none": "Unknown"}:
                return 4, str(destination_group_jid) + "@groups.kik.com"
            else:
                with open(self.config["paths"]["backup"] + str(source_group_jid) + '/database.json',
                          'r') as import_file:
                    backup_data = json.load(import_file)
                    group_settings = json.loads(backup_data[0]["group_settings"])

                    group_messages = json.loads(backup_data[0]["group_messages"])
                    censor_words = json.loads(backup_data[0]["censor_words"])
                    admin_triggers = json.loads(backup_data[0]["admin_triggers"])
                    user_triggers = json.loads(backup_data[0]["user_triggers"])
                    group_settings["join_time"] = group_settings_dst["join_time"]
                    if os.path.exists(self.config["paths"]["trigger_media"] + str(source_group_jid)):
                        source = self.config["paths"]["trigger_media"] + str(source_group_jid)
                        if os.path.exists(self.config["paths"]["trigger_media"] + str(destination_group_jid)):
                            shutil.rmtree(
                                self.config["paths"]["trigger_media"] + str(destination_group_jid) + "@groups.kik.com/")
                        dest = self.config["paths"]["trigger_media"] + str(destination_group_jid) + "@groups.kik.com/"
                        shutil.copytree(source, dest)
                    if os.path.exists(self.config["paths"]["message_media"] + str(source_group_jid)):
                        source = self.config["paths"]["message_media"] + str(source_group_jid)
                        if os.path.exists(self.config["paths"]["message_media"] + str(destination_group_jid)):
                            shutil.rmtree(
                                self.config["paths"]["message_media"] + str(destination_group_jid) + "@groups.kik.com/")
                        dest = self.config["paths"]["message_media"] + str(destination_group_jid) + "@groups.kik.com/"
                        shutil.copytree(source, dest)

                    Database(self.config).remove_group(str(destination_group_jid))
                    Database(self.config).add_group_to_database(str(destination_group_jid), destination_hash,
                                                                dest_group_data[0][1], group_settings, group_messages,
                                                                owner,
                                                                admins, members, user_triggers, admin_triggers,
                                                                censor_words, bot_id)
                    import_file.close()
                    Database(self.config).load_single_group_cache(destination_group_jid)
                return 1, str(destination_group_jid) + "@groups.kik.com"

    def restore_group_database(self, peer_jid, group_jid, bot_id):
        group_data = RedisCache(self.config).get_all_group_data(group_jid)
        group_admins = group_data["group_admins"]
        bot_admins = RedisCache(self.config).get_bot_config_data("json", "bot_admins", bot_id)
        all_admins = {**bot_admins, **group_admins}
        if peer_jid in all_admins:
            self.cursor.execute(
                "SELECT group_owner, group_admins, group_members FROM group_data WHERE group_jid = %s",
                (group_jid.split('@')[0],))
            member_list = self.cursor.fetchall()
            owner = {}
            admins = {"none": "Unknown"}
            members = {}

            if is_json(member_list[0][0]):
                owner = json.loads(member_list[0][0])
            if is_json(member_list[0][1]):
                admins = json.loads(member_list[0][1])
            if is_json(member_list[0][2]):
                members = json.loads(member_list[0][2])
            if admins == {"none": "Unknown"}:
                return 4
            else:

                with open(self.config["paths"]["backup"] + group_jid + '/database.json', 'r') as import_file:
                    group_data = json.load(import_file)
                    group_settings = json.loads(group_data[0]["group_settings"])
                    group_messages = json.loads(group_data[0]["group_messages"])
                    censor_words = json.loads(group_data[0]["censor_words"])
                    admin_triggers = json.loads(group_data[0]["admin_triggers"])
                    user_triggers = json.loads(group_data[0]["user_triggers"])
                    last_group_members = json.loads(group_data[0]["group_members"])

                    for m in members:
                        if m in last_group_members:
                            if last_group_members[m]["level"] <= members[m]["level"]:
                                last_group_members[m]["level"] = members[m]["level"]
                            if last_group_members[m]["xp"] <= members[m]["xp"]:
                                last_group_members[m]["xp"] = members[m]["xp"]
                            if last_group_members[m]["currency"] <= members[m]["currency"]:
                                last_group_members[m]["currency"] = members[m]["currency"]

                        if m not in last_group_members:
                            last_group_members[m] = members[m]

                    if os.path.exists(self.config["paths"]["backup"] + group_jid + "/trigger"):
                        source = self.config["paths"]["backup"] + group_jid + "/trigger"
                        if os.path.exists(self.config["paths"]["trigger_media"] + group_jid):
                            shutil.rmtree(self.config["paths"]["trigger_media"] + group_jid)
                        dest = self.config["paths"]["trigger_media"] + group_jid + "/"
                        shutil.copytree(source, dest)

                    if os.path.exists(self.config["paths"]["backup"] + group_jid + "/message"):
                        source = self.config["paths"]["backup"] + group_jid + "/message"
                        if os.path.exists(self.config["paths"]["message_media"] + group_jid):
                            shutil.rmtree(self.config["paths"]["message_media"] + group_jid)
                        dest = self.config["paths"]["message_media"] + group_jid + "/"
                        shutil.copytree(source, dest)

                    Database(self.config).remove_group(group_jid)
                    Database(self.config).add_group_to_database(group_jid.split('@')[0], group_data[0]["group_hash"],
                                                     group_data[0]["group_name"], group_settings, group_messages, owner,
                                                     admins, last_group_members, user_triggers, admin_triggers,
                                                     censor_words, bot_id)
                    import_file.close()
                    Database(self.config).load_single_group_cache(group_jid)
                    return 1
        else:
            return 2
