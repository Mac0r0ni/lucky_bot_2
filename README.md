# Lucky Kik Bot




### Installation:

Requirements:

Linux Server OS

MySQL Server

Redis Server

Python 3 Either 3.6, 3.7, or 3.8


### Step 1
- Move bot_config_sample.json to bot_config.json
- Move bot_credentials_sample.json to 


### Configure Python 3
- install included Unofficial KIK API
```pip install ./kik_unofficial_api```
- Install Python 3 Libraries ```pip install -r requirements.txt```



### Configure MySQL
- Create a MYSQL User and an Empty database for that user. 
- Add mysql host/port/username/password/databse name to bot_config.json
- run python3 init_database.py



### Configure Redis
- Install Redis Server
- Add Redis host/port/password (if using password) to bot_config.json




### Create a Bot

- Create a KIK account for the bot. Set name profile picture/background as you would normally
- Run ```python3 init_bot.py kik_username kik_password bot_id```
Where kik_username is the username you set for the kik account and password is the password for the kik account. Bot id is a number between 1-9999 that will be this bots id number.




### Run Bot
```python3 main.py kik_username```


