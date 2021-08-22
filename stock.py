import subprocess
import json
import signal
import sys
import time
import random
import requests
import discord
from discord.ext import tasks 
from shutil import which

prevProducts = {}

#
# User Interface stuff
#
def signal_handler():
    print('\033[?1049l')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
print('\033[?1049h')



#
# Discord stuff
#
TOKEN = open("token.txt","r").readline()
client = discord.Client()
start = time.time()

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    loop_task.start()
    channel = client.get_channel(877946391647903876)
    await channel.send("Hello!")

@tasks.loop(seconds = 10)
async def loop_task():
    await check_stock()



#
# Stock checking stuff
#
async def check_stock():
    global prevProducts
    channel = client.get_channel(877946391647903876)
    print('\033[2J\033[3J\033[1;1HLoading...')

    try:
        # using curl seems to get blocked less often
        if which("curl") is not None:
            response = subprocess.check_output(['curl', '-s',
                "https://api.nvidia.partners/edge/product/search?page=1&limit=9&locale=en-gb&category=GPU&manufacturer=NVIDIA&manufacturer_filter=NVIDIA~6,3XS%20SYSTEMS~0,ACER~0,AORUS~4,ASUS~43,DELL~0,EVGA~18,GAINWARD~1,GIGABYTE~48,HP~0,INNO3D~6,LENOVO~0,MSI~31,NOVATECH~0,PALIT~17,PC%20SPECIALIST~0,PNY~4,RAZER~0,ZOTAC~21",
                "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
                "-H", "Accept-Language: en-GB,en-US;q=0.7,en;q=0.3",
                "--max-time", "5",
                "--compressed"
                ], shell=False)
        else:
            url = "https://api.nvidia.partners/edge/product/search?page=1&limit=9&locale=en-gb&category=GPU&manufacturer=NVIDIA&manufacturer_filter=NVIDIA~6,3XS%20SYSTEMS~0,ACER~0,AORUS~4,ASUS~43,DELL~0,EVGA~18,GAINWARD~1,GIGABYTE~48,HP~0,INNO3D~6,LENOVO~0,MSI~31,NOVATECH~0,PALIT~17,PC%20SPECIALIST~0,PNY~4,RAZER~0,ZOTAC~21"
            headers = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",}
            response = requests.get(url, headers = headers, timeout = 5).content
    except Exception as e:
        print("API request failed " + e)
        await channel.send("API request failed " + e)
        randTime = round(60 + random.uniform(0, 10))
        loop_task.change_interval(seconds = randTime)
        return

    responseData = response.decode('utf8').replace("'", '"')
    jsonDict = json.loads(responseData)

    featured = jsonDict["searchedProducts"]["featuredProduct"]
    products = jsonDict["searchedProducts"]["productDetails"]
    products.append(featured)
    print('\033[1;1H\033[2K')

    for i, product in enumerate(products):
        print(product["displayName"], end=' ')

        if product["prdStatus"] == 'out_of_stock':
            print('\033[31m' + product["prdStatus"] + '\033[0m', end=' ')
        else:
            print('\033[32;5m' + product["prdStatus"] + '\033[0m', end=' ')

            if prevProducts != {} and product != prevProducts[i]:
                await channel.send(product["displayName"] + ' ' + 
                                    product["prdStatus"] + ' ' + 
                                    product["retailers"][0]["purchaseLink"])

        print(product["retailers"][0]["purchaseLink"])

    prevProducts = products
    randTime = round(10 + random.uniform(0, 10))
    loop_task.change_interval(seconds = randTime)
    print('\033[1G\033[2K' + f"{randTime}", end=' ', flush=True)


client.run(TOKEN)
