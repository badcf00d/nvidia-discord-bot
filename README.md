# nvidia-discord-bot
A stock tracker for rtx cards

#### token.txt
Just a text file with your bot token on the first line

#### channels.txt
 - Uses the format: `<channel id>,<list of locales, hyphen-seperated>`, e.g:
 ```123123123123123,UK-FR-DE
 234234234234234,UK
 345345345345345,UK-FR
 ```
 - The first server in the list also receives error reports


#### Linux setup
```bash
sudo apt install python3-pip python3-dev
git clone https://github.com/badcf00d/nvidia-discord-bot.git
cd nvidia-discord-bot/
pip3 install -r requirements.txt
# Place your bot token in token.txt
# Place your channel ID in channels.txt
python3 stock.py
```
