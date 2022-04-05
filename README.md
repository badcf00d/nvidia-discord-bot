# nvidia-discord-bot
A stock tracker for rtx cards

#### Linux setup
```bash
sudo apt install python3-pip python3-dev
git clone https://github.com/badcf00d/nvidia-discord-bot.git
cd nvidia-discord-bot/
pip3 install -r requirements.txt
# Place your bot token in token.txt, or BOT_TOKEN environmental variable
# Place your channel ID in channels.txt, or BOT_CHANNELS environmental variable
python3 stock.py
```

#### Docker Setup
- Install Docker: https://docs.docker.com/get-docker/
- Install Docker-Compose: https://docs.docker.com/compose/install/
- Place your bot token in token.txt, or BOT_TOKEN environmental variable
- Place your channel ID in channels.txt, or BOT_CHANNELS environmental variable
- To start: `docker-compose up`
- To close: `docker-compose down`

#### token.txt
Just a text file with your bot token on the first line

#### channels.txt
 - Uses the format: `<channel id>,<receive debug messages>,<colon-seperated list of locales>;`, e.g:
 ```
 123123123123123,true,en-gb:FR:DE;
 234234234234234,false,en-gb;
 345345345345345,false,en-gb:FR;
 ```
