import subprocess
import json
import signal
import time
import random
import requests
import discord
import asyncio
import os
from discord.ext import tasks
from shutil import which
from pathlib import Path

skus = ['NVGFT080', 'NVGFT090', 'NVGFT070', 'NVGFT060T', 'NVGFT070T', 'NVGFT080T', 'NVGFT090T']
class Locale:
    index = 0
    schedule = ['en-gb', 'DE', 'en-gb', 'FR', 'en-gb', None]
class Channel:
    def __init__(self, id, debug, locales):
        self.id = id
        self.debug = debug
        self.locales = locales

prevProducts = {}
lastResponse = time.time()
client = discord.Client()
channelIds = []
channelList = []
notifyOnStartup = os.environ.get('NOTIFY_ON_STARTUP') is not None

if os.environ.get('BOT_TOKEN') is not None:
    TOKEN = os.environ.get('BOT_TOKEN')
else:
    TOKEN = open(Path(__file__).with_name('token.txt'),'r').readline()

if os.environ.get('BOT_CHANNELS') is not None:
    channelFile = os.environ.get('BOT_CHANNELS')
else:
    channelFile = open(Path(__file__).with_name('channels.txt'),'r').read().replace('\r','').replace('\n','')

for channel in channelFile.split(';'):
    fields = channel.split(',')
    if len(fields) >= 3:
        channelIds.append(Channel(int(fields[0]), fields[1].lower() == 'true', fields[2]))


#
# User Interface stuff
#
async def signal_handler():
    global channelList
    print('\033[1;1H\033[2K\033[?1049l')
    print('Logging out and closing')
    try:
        for channel in channelList:
            if channel.debug == True:
                await channel.id.send('Shutting down')
    except Exception:
        pass
    await client.close()
    asyncio.get_event_loop().stop()

print('\033[?1049h\033[1;1H\033[2K')




#
# Discord stuff
#
@client.event
async def on_ready():
    global channelList

    if loop_task.is_running():
        print("Discord.py reconnected itself")
        return

    print('Logged in as {0.user}'.format(client))

    if os.name == 'posix':
        for signame in ('SIGINT', 'SIGTERM'):
            client.loop.add_signal_handler(getattr(signal, signame),
                                    lambda: asyncio.ensure_future(signal_handler()))
    for channelId in channelIds:
        channelList.append(Channel(client.get_channel(channelId.id), channelId.debug, channelId.locales))

    try:
        for channel in channelList:
            if channel.debug == True:
                await channel.id.send('Hello!')
    except Exception as e:
        print('Welcome message failed: ' + repr(e))

    print('Waiting 61 seconds to start:')
    for i in range(61):
        print(str(i) + ', ', end='', flush=True)
        await asyncio.sleep(1)
    loop_task.start()

@tasks.loop(seconds = 5)
async def loop_task():
    await check_stock()

@client.event
async def on_message(message):
    global prevProducts, lastResponse

    if message.author != client.user and client.user.mentioned_in(message):
        if prevProducts == {}:
            try:
                await message.reply('Not checked Nvidia yet')
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
                await message.reply(reply)
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
    if 'NVGFT090T_' in sku:
        return 'RTX 3090 Ti'
    if 'NVGFT090_' in sku:
        return 'RTX 3090'
    elif 'NVGFT080T_' in sku:
        return 'RTX 3080 Ti'
    elif 'NVGFT080_' in sku:
        return 'RTX 3080'
    elif 'NVGFT070T_' in sku:
        return 'RTX 3070 Ti'
    elif 'NVGFT070_' in sku:
        return 'RTX 3070'
    elif 'NVGFT060T_' in sku:
        return 'RTX 3060 Ti'
    else:
        return sku


async def send_message(productName, product):
    global channelList
    currentLocale = Locale.schedule[Locale.index]

    message = '[' + currentLocale.replace('en-gb', 'UK') + '] ' + productName + ' '
    if 'true' in product['is_active']:
        message += 'In stock: '
    elif 'false' in product['is_active']:
        message += 'Out of stock: '
    else:
        message += product['is_active'] + ': '
    message += product['product_url']

    try:
        for channel in channelList:
            if currentLocale in channel.locales:
                await channel.id.send(message)
    except Exception as e:
        print('Stock alert failed: ' + repr(e))


async def parse_response(jsonDict):
    global channelList
    currentLocale = Locale.schedule[Locale.index]
    products = {}

    for product in jsonDict:
        if 'NVGFT' in product['fe_sku']:
            products[product['fe_sku']] = product
    print('\033[1;1H\033[2K')

    for sku, product in products.items():
        productName = get_product_name(sku)
        if currentLocale == 'en-gb':
            product['product_url'] = f'https://store.nvidia.com/en-gb/geforce/store/gpu/?page=1&limit=100&locale=en-gb&category=GPU&gpu={productName}&manufacturer=NVIDIA'.replace(' ', '%20')
        url = product['product_url'].lower()
        state = product['is_active'].lower()
        print(productName, end=' ')

        if state == 'false':
            print('\033[31m' + state + '\033[0m', end=' ')
        else:
            print('\033[32;5m' + state + '\033[0m', end=' ')

        if (currentLocale in prevProducts) and (sku in prevProducts[currentLocale]):
            prevUrl = prevProducts[currentLocale][sku]['product_url'].lower()
            prevState = prevProducts[currentLocale][sku]['is_active'].lower()
            if ((state == 'true') and (state != prevState)) or (state == 'true' and (url != prevUrl)):
                await send_message(productName, product)
        elif (notifyOnStartup) and (state == 'true'):
            await send_message(productName, product)

        print(product['product_url'])
    return products


async def check_stock():
    global prevProducts, lastResponse, channelList, skus

    try:
        currentLocale = Locale.schedule[Locale.index]
        jsonDict = {}
        print('\033[2J\033[3J\033[1;1HLoading...')

        for sku in skus:
            # using curl seems to get blocked less often
            if which('curl') is not None and os.name == 'posix':
                response = subprocess.check_output(['curl', '-s',
                    f'https://api.store.nvidia.com/partner/v1/feinventory?skus={sku}&locale={currentLocale}',
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                    '-H', 'Accept-Language: en-GB,en-US;q=0.7,en;q=0.3',
                    '--max-time', '10',
                    '--compressed'
                    ], shell=False).decode().replace("'", '"')
            else:
                url = f'https://api.store.nvidia.com/partner/v1/feinventory?skus={sku}&locale={currentLocale}'
                headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                        'Accept-Language': 'en-GB,en-US;q=0.7,en;q=0.3'}
                response = requests.get(url, headers = headers, timeout = 10).content.decode().replace("'", '"')

            if jsonDict:
                jsonDict.extend(json.loads(response)['listMap'])
            else:
                jsonDict = json.loads(response)['listMap']

        prevProducts[currentLocale] = await parse_response(jsonDict)
        cycle_locale()
        lastResponse = time.time()

        randTime = round(4 + random.uniform(0, 1))
        loop_task.change_interval(seconds = randTime)
        print('\033[1G\033[2K' + f'{randTime}', end=' ', flush=True)

    except Exception as e:
        print('API request failed:\n' + repr(e) + '\n\nResponse:\n' + (repr(response) if 'response' in locals() and response is not None else '(null)'))
        try:
            for channel in channelList:
                if channel.debug == True and (time.time() - lastResponse) > 60:
                    await channel.id.send('API request failed:\n' + repr(e) + '\n\nResponse:\n' + (repr(response) if 'response' in locals() and response is not None else '(null)'))
                if channel.debug == True and (time.time() - lastResponse) > 300:
                    await channel.id.send('No response received for 5 minutes, quitting')
            if ((time.time() - lastResponse) > 300):
                signal.raise_signal(signal.SIGINT)
        except Exception as e:
            print('Fail notification failed: ' + repr(e))

        loop_task.change_interval(seconds = 61)


client.run(TOKEN)
