# Python 3 Core Libraries
import subprocess
import sys
import time
import random
import string

# Python 3 Third Party Libraries


# Python 3 Project Libraries
from lib.email_handler import send_email
from lib.redis_handler import RedisCache


def heartbeat_loop(client, config, bot_name, bot_id):
    count = 0
    while True:
        time.sleep(60)
        random_length = random.randint(3, 11)
        random_name = ''.join(random.choices(string.ascii_lowercase, k=random_length))
        heartbeat_queue = RedisCache(config).get_heartbeat_data(bot_id)

        if heartbeat_queue and "received" in heartbeat_queue:
            if count > 0 and heartbeat_queue["received"] is not False:
                count = 0
            elif count < 2 and heartbeat_queue["received"] is False:
                print("step 3 count: " + str(count))
                count += 1
            elif heartbeat_queue["received"] is False:
                heartbeat_queue["offline"] = True
                RedisCache(config).update_heartbeat_data(heartbeat_queue, bot_id)
                send_email(config, "offline", bot_name, bot_id)
                command = "./home/lucky/lucky_bot/lucky.sh start lucky_bot_" + bot_id
                command_format = command.split(" ")
                result = subprocess.run(
                    # Command as a list, to avoid shell=True
                    command_format,
                    # Expect textual output, not bytes; let Python .decode() on the fly
                    text=True,
                    # Shorthand for stdout=PIPE stderr=PIPE etc etc
                    capture_output=True,
                    # Raise an exception if ping fails (maybe try/except it separately?)
                    check=True)
                sys.exit(1)
        heartbeat_queue = {"time": time.time(), "received": False, "offline": False, "captcha": False,
                           "temp_ban": False, "temp_ban_time": 0, "recovered": False, "count": count,
                           "reported": False, "report_time": 0}
        RedisCache(config).update_heartbeat_data(heartbeat_queue, bot_id)
        client.check_username_uniqueness(random_name, True)
