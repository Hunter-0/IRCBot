import socket
import time
import sys

openpw = open("password.txt", "r")   # Password for twitch
pw = (openpw.read()).strip()
OAUTH = 'oauth:'+pw  # Get this from https://twitchapps.com/tmi/
NICK = 'Enter Username'  # https://dev.twitch.tv/docs/irc/guide#twitch-irc-capabilities
CHANNEL = ("Channel1", "Channel2")
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect(('irc.chat.twitch.tv', 6667))


def joinchannels():
    for i in CHANNEL:
        irc.send(bytes(f'JOIN #{i}\r\n', 'UTF-8'))


irc.send(bytes(f'PASS {OAUTH}\r\n', 'UTF-8'))
irc.send(bytes(f'NICK {NICK}\r\n', 'UTF-8'))
joinchannels()
buffer = ''
startdate = time.time()
startTime = time.time()
print("Bot Started")


def sendmsg(channel, message):
    irc.send(bytes(f'PRIVMSG #{channel} :{message}\r\n', 'UTF-8'))


def processTwitchLine(inp):
    if inp == "PING :tmi.twitch.tv":
        print('ponging')
        irc.send(bytes(f'PONG :tmi.twitch.tv\r\n', 'UTF-8'))
    if inp == ":tmi.twitch.tv RECONNECT":
        print("Reconnecting.")
        exit()
    index = inp.find('!')
    index2 = inp.find(' :')
    index3 = inp.find(' #')
    currentchannel0 = inp[index3:]
    index4 = currentchannel0.find(':')
    user = inp[1:index]
    message1 = inp[index2:]
    message = message1[2:]
    currentchannel1 = currentchannel0[2:index4]
    currentchannel = currentchannel1[0:-1]

    admin = ["Enter Admin Name"]
    if user in admin:
        if message.startswith("*shutdown"):
            print("Shutting down.")
            sys.exit()


while True:
    while True:
            buffer += irc.recv(2048).decode("UTF-8", errors="ignore")
            split = buffer.split('\r\n')
            splitLen = len(split)
            if splitLen >= 2:
                for currentLine in split[:-1]:
                    processTwitchLine(currentLine)  # process each line
                buffer = split[-1]
