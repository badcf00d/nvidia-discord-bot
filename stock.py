import subprocess
import json
import signal
import time
import random
import requests
import discord
import asyncio
from discord.ext import tasks 
from shutil import which
from pathlib import Path

class Locale:
    index = 0
    schedule = ['UK', 'DE', 'UK', 'FR', 'UK', None]

TOKEN = open(Path(__file__).with_name('token.txt'),'r').readline()
CHANNEL_ID = int(open(Path(__file__).with_name('channel.txt'),'r').readline())
prevProducts = {}
lastResponse = 0
client = discord.Client()



#
# User Interface stuff
#
async def signal_handler():
    channel = client.get_channel(CHANNEL_ID)
    print('\033[?1049l')
    print('Logging out and closing')
    try:
        await channel.send('Bot closing ')
    except Exception:
        pass
    await client.close()
    asyncio.get_event_loop().stop()
    
print('\033[?1049h')




#
# Discord stuff
#
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    for signame in ('SIGINT', 'SIGTERM'):
        client.loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.ensure_future(signal_handler()))

    loop_task.start()
    channel = client.get_channel(CHANNEL_ID)
    await channel.send('Hello!')

@tasks.loop(seconds = 10)
async def loop_task():
    await check_stock()

@client.event
async def on_message(message):
    global prevProducts, lastResponse
    channel = client.get_channel(CHANNEL_ID)

    if message.author != client.user:
        if prevProducts == {}:
            try:
                await channel.send('Not checked Nvidia yet')
            except Exception as e:
                print('Reply failed: ' + repr(e))
        else:
            reply = 'Last response: ' + time.ctime(lastResponse) + '\n'
            for locale, products in prevProducts.items():
                reply += locale + '\n'
                for product in products:
                    reply += get_product_name(product['fe_sku']) + ' '
                    reply += product['is_active'] + ' '
                    reply += product['product_url'] + '\n'

            try:
                await channel.send(reply)
            except Exception as e:
                print('Reply failed: ' + repr(e))




#
# Stock checking stuff
#
def cycle_locale():
    nextLocale = Locale.schedule[Locale.index]
    Locale.index += 1
    if Locale.schedule[Locale.index] is None:
        Locale.index = 0
    return nextLocale


def get_product_name(sku):
    if 'NVGFT090_' in sku:
        return 'RTX 3090'
    elif 'NVGFT080T_' in sku:
        return 'RTX 3080Ti'
    elif 'NVGFT080_' in sku:
        return 'RTX 3080'
    elif 'NVGFT070T_' in sku:
        return 'RTX 3070Ti'
    elif 'NVGFT070_' in sku:
        return 'RTX 3070'
    elif 'NVGFT060T_' in sku:
        return 'RTX 3060Ti'
    else:
        return sku


async def parse_response(response, channel):
    responseData = response.decode('utf8').replace("'", '"')
    currentLocale = Locale.schedule[Locale.index]
    jsonDict = json.loads(responseData)
    products = []

    for product in jsonDict['listMap']:
        if 'NVGFT' in product['fe_sku']:
            products.append(product)
    print('\033[1;1H\033[2K')

    for i, product in enumerate(products):
        productName = get_product_name(product['fe_sku'])
        print(productName, end=' ')

        if product['is_active'] == 'false':
            print('\033[31m' + product['is_active'] + '\033[0m', end=' ')
        else:
            print('\033[32;5m' + product['is_active'] + '\033[0m', end=' ')

            if currentLocale not in prevProducts or product != prevProducts[currentLocale][i]:
                message = productName + ' '
                message += product['is_active'] + ' '
                message += product['product_url']
                try:
                    await channel.send(message)
                except Exception as e:
                    print('Stock alert failed: ' + repr(e))

        print(product['product_url'])
    return products


async def check_stock():
    global prevProducts, lastResponse
    channel = client.get_channel(CHANNEL_ID)
    currentLocale = Locale.schedule[Locale.index]

    print('\033[2J\033[3J\033[1;1HLoading...')

    try:
        # using curl seems to get blocked less often
        if which('curl') is not None:
            response = subprocess.check_output(['curl', '-s',
                f'https://api.store.nvidia.com/partner/v1/feinventory?skus={currentLocale}~NVGFT090~NVGFT080T~NVGFT080~NVGFT070T~NVGFT070~NVGFT060T~187&locale={currentLocale}',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                '-H', 'Accept-Language: en-GB,en-US;q=0.7,en;q=0.3',
                '--max-time', '10',
                '--compressed'
                ], shell=False)
        else:
            url = f'https://api.store.nvidia.com/partner/v1/feinventory?skus={currentLocale}~NVGFT090~NVGFT080T~NVGFT080~NVGFT070T~NVGFT070~NVGFT060T~187&locale={currentLocale}',
            headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                       'Accept-Language': 'en-GB,en-US;q=0.7,en;q=0.3'}
            response = requests.get(url, headers = headers, timeout = 10).content
    except Exception as e:
        print('API request failed ' + repr(e))
        try:
            await channel.send('API request failed ' + repr(e))
        except Exception as e:
            print('Fail notification failed: ' + repr(e))
        randTime = round(60 + random.uniform(0, 10))
        loop_task.change_interval(seconds = randTime)
        return

    prevProducts[currentLocale] = await parse_response(response, channel)
    cycle_locale()
    lastResponse = time.time()

    randTime = round(10 + random.uniform(0, 7))
    loop_task.change_interval(seconds = randTime)
    print('\033[1G\033[2K' + f'{randTime}', end=' ', flush=True)


client.run(TOKEN)
