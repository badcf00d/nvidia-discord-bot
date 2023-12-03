#!/usr/bin/python3
import signal
import time
import random
import discord
import asyncio
import os
import urllib.request
from discord.ext import tasks
from pathlib import Path
from bs4 import BeautifulSoup

class Channel:
    def __init__(self, id, debug):
        self.id = id
        self.debug = debug

prevStatus = None
lastResponse = time.time()
client = discord.Client(intents=discord.Intents.default())
channelIds = []
channelList = []
notifyOnStartup = os.environ.get('NOTIFY_ON_STARTUP') is not None

MSFT_URL = 'https://www.microsoft.com/en-gb/d/windows-dev-kit-2023/94k0p67w7581?activetab=pivot:overviewtab'

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
    if len(fields) >= 2:
        channelIds.append(Channel(int(fields[0]), fields[1].lower() == 'true'))


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
        channelList.append(Channel(client.get_channel(channelId.id), channelId.debug))

    try:
        for channel in channelList:
            if channel.debug == True:
                await channel.id.send('Hello!')
    except Exception as e:
        print('Welcome message failed: ' + repr(e))

    # print('Waiting 61 seconds to start:')
    # for i in range(61):
    #    print(str(i) + ', ', end='', flush=True)
    #    await asyncio.sleep(1)
    loop_task.start()

@tasks.loop(seconds = 300)
async def loop_task():
    await check_stock()

@client.event
async def on_message(message):
    global prevProducts, lastResponse

    if message.author != client.user and client.user.mentioned_in(message):
        if prevProducts == {}:
            try:
                await message.reply('Not checked Windows yet')
            except Exception as e:
                print('Reply failed: ' + repr(e))
        else:
            reply = 'Last response: ' + time.ctime(lastResponse) + '\n' + prevStatus

            try:
                await message.reply(reply)
            except Exception as e:
                print('Reply failed: ' + repr(e))
            reply = ''
            await asyncio.sleep(1)




#
# Stock checking stuff
#



async def send_message(in_stock: bool):
    global channelList

    message = f'Microsoft Dev Kit {"In Stock " if (in_stock) else "Out of stock "}: {MSFT_URL}'

    try:
        for channel in channelList:
            await channel.id.send(message)
    except Exception as e:
        print('Stock alert failed: ' + repr(e))


async def parse_response(currentStatus: bool):
    global prevStatus
 
    if (prevStatus != None) and (currentStatus != prevStatus):
        await send_message(currentStatus)
    elif (prevStatus == None) and (notifyOnStartup):
        await send_message(currentStatus)


async def check_stock():
    global prevProducts, lastResponse, channelList, prevStatus

    try:
        
        print('\nLoading...')

        response = urllib.request.urlopen(MSFT_URL).read()
        soup = BeautifulSoup(response, 'html.parser')
        statusText = soup.find(attrs={"data-automation-test-id" : "buy-box-cta-description"}).text
        
        status = "Out of stock" not in statusText
        
        print(f'Microsoft Dev Kit {statusText}: {MSFT_URL}')
        await parse_response(status)
        prevStatus = status

        lastResponse = time.time()
        randTime = round(30 + random.uniform(0, 10))
        loop_task.change_interval(seconds = randTime)
        print(f'{randTime}')

    except Exception as e:
        print('API request failed:\n' + repr(e) + '\n\nResponse:\n' + (repr(response) if 'response' in locals() and response is not None else '(null)'))
        try:
            for channel in channelList:
                if channel.debug == True and (time.time() - lastResponse) > 60:
                    await channel.id.send('API request failed:\n' + repr(e) + '\n\nResponse:\n' + (repr(response) if 'response' in locals() and response is not None else '(null)'))
                if channel.debug == True and (time.time() - lastResponse) > 300:
                    await channel.id.send('No response received for 5 minutes, quitting')
        except Exception as e:
            print('Fail notification failed: ' + repr(e))

        if ((time.time() - lastResponse) > 300):
            signal.raise_signal(signal.SIGINT)
        loop_task.change_interval(seconds = 61)


client.run(TOKEN)
