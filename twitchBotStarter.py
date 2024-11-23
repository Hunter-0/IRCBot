import socket
import time
import wolframalpha
import datetime as datetime
import random
from cookies import cookielist # From own file
import json
import praw
import os
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
print("Bot Started")

# Files for saving our data
with open('afkfileT.json', 'r') as afkfile: afk_status = json.loads(afkfile.read())
with open('sleepfileT.json', 'r') as sleepfile: sleep_status = json.loads(sleepfile.read())
with open('timefileT.json', 'r') as timefile: time_status = json.loads(timefile.read())
with open('remindfileT.json', 'r') as remindfile: remind_status = json.loads(remindfile.read())


def sendmsg(channel, message):
    irc.send(bytes(f'PRIVMSG #{channel} :{message}\r\n', 'UTF-8'))


def sendmsglong(channel, themessage):  # When the message takes up multiple chat messages
    if len(themessage) > 450:
        print(len(themessage))
        new_line_string = '\n\n\n'
        messages = [themessage[i:i+450] for i in range(0, len(themessage), 450)]
        for i in messages:
            modified_message = i.replace('\n\n', new_line_string)
            irc.send(bytes(f'PRIVMSG #{channel} :{modified_message}\r\n', 'UTF-8'))
            time.sleep(2)
    else:
        irc.send(bytes(f'PRIVMSG #{channel} :{themessage}\r\n', 'UTF-8'))

# For query command
def wolfram(themessage):
    client = wolframalpha.Client("Enter Client ID")
    question = themessage

    result = client.query(input=question, ip="Enter IP")

    if result["@success"] == "false":

        return "Error processing your request"
    else:
        try:
            result_text = next(result.results).text.replace("\n", " ")
            return result_text
        except StopIteration:
            return "No proper answer was found for your query."


history_file = 'processed_posts.txt'

# Initialize Reddit API client, can use for example to send message in chat when new post appears
reddit = praw.Reddit(client_id='Enter',
                     client_secret='Enter',
                     user_agent='Enter')

subreddit_name = ''


def load_history():
    if not os.path.exists(history_file):
        return set()
    with open(history_file, 'r') as f:
        return set(line.strip() for line in f)


def save_history(processed_ids):
    with open(history_file, 'w') as f:
        for post_id in processed_ids:
            f.write(f"{post_id}\n")


def check_new_posts(reddit, subreddit_name, processed_ids):
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=15):
        # Makes sure the post is at 10 minutes old and not already processed
        if (time.time() - submission.created_utc > 600) and (submission.id not in processed_ids):
            # Construct full URL
            comments_url = f"https://www.reddit.com{submission.permalink}"
            sendmsg("Enter Channel Name", f"{comments_url}")
            processed_ids.add(submission.id)
    return processed_ids


startTime = time.time()


def timereply(message, user, messagetime, thestatus, currentchannel):
    time_difference = int(messagetime - thestatus[user]['time'])
    minutes = "minutes"
    seconds = "seconds"
    hours = "hours"
    days2 = "days"
    seconds2 = time_difference
    if seconds2 < 60:
        sendmsg(currentchannel, message.format(user, thestatus[user]["reason"], int(seconds2), 'seconds', "", ""))
    elif 60 <= time_difference <= 3600:
        mins, secs = divmod(time.time() - thestatus[user]['time'], 60)
        if int(mins) < 2:
            minutes = "minute"
        if int(secs) < 2:
            seconds = "second"                                  # user,reason,m,m,s,s
        sendmsg(currentchannel, message.format(user, thestatus[user]["reason"], int(mins), minutes, int(secs), seconds))
    elif 3600 <= time_difference <= 86400:
        hrs, mins = divmod(time.time() - thestatus[user]['time'], 3600)
        if int(mins) < 2:
            minutes = "minute"
        if int(hrs) < 2:
            hours = "hour"
        sendmsg(currentchannel, message.format(user, thestatus[user]["reason"], int(hrs), hours, int(mins / 60), minutes))
    elif time_difference >= 86400:
        days, hrs = divmod(time.time() - thestatus[user]['time'], 86400)
        if int(hrs) < 2:
            hours = "hour"
        if int(days) < 2:
            days2 = "day"
        sendmsg(currentchannel, message.format(user, thestatus[user]["reason"], int(days), days2, int(hrs / 3600), hours))


timelast = 4


def processTwitchLine(inp):
    # print(inp)
    global timelast
    global afk_status
    global sleep_status
    global remind_status
    global recent
    global remindcount
    if inp == "PING :tmi.twitch.tv":
        print('ponging')
        irc.send(bytes(f'PONG :tmi.twitch.tv\r\n', 'UTF-8'))
    if inp == ":tmi.twitch.tv RECONNECT":
        afkfile = json.dumps(afk_status)
        sleepfile = json.dumps(sleep_status)
        timefile = json.dumps(time_status)
        remindfile = json.dumps(remind_status)
        afk = open('afkfileT.json', 'w')
        afk.write(afkfile)
        afk.close()
        sleep = open('sleepfileT.json', 'w')
        sleep.write(sleepfile)
        sleep.close()
        timey = open('timefileT.json', 'w')
        timey.write(timefile)
        timey.close()
        remind = open('remindfileT.json', 'w')
        remind.write(remindfile)
        remind.close()
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
    currentchannel1 = currentchannel0[2:index4]  # recent = message
    currentchannel = currentchannel1[0:-1]
    messagetime = time.time()
    remindeduser = user

    admin = ["Enter Admin Name"]
    if user in admin:
        if message.startswith("*shutdown"):
            afkfile = json.dumps(afk_status)
            sleepfile = json.dumps(sleep_status)
            timefile = json.dumps(time_status)
            remindfile = json.dumps(remind_status)
            afk = open('afkfileT.json', 'w')
            afk.write(afkfile)
            afk.close()
            sleep = open('sleepfileT.json', 'w')
            sleep.write(sleepfile)
            sleep.close()
            timey = open('timefileT.json', 'w')
            timey.write(timefile)
            timey.close()
            remind = open('remindfileT.json', 'w')
            remind.write(remindfile)
            remind.close()
            print("Shutting down.")
            sys.exit()

        if message.startswith('*p '):
            pyr0 = message.replace('*p', '').strip()
            pyr = pyr0+" "
            bla = " "
            sendmsg(currentchannel, pyr)
            sendmsg(currentchannel, pyr + bla + pyr)
            sendmsg(currentchannel, pyr + bla + pyr + bla + pyr)
            sendmsg(currentchannel, pyr + bla + pyr)
            sendmsg(currentchannel, pyr)

    if remindeduser in remind_status:
        if remind_status[remindeduser]['remind']:
            remind_status[remindeduser]['remind'] = False  # clear?
            msgs = ""
            for x in remind_status["reminders"][remindeduser]:
                msg = (remind_status["reminders"][remindeduser][x])
                msgs = msg + msgs

            sendmsglong(currentchannel, '{} has the following reminders: {}'.format(remindeduser, msgs))
            remind_status["reminders"][remindeduser].clear()

    if message.startswith('*remind') or message.startswith('*r '):
        if time.time() - timelast >= 3:
            timelast = time.time()
            reason0 = message.replace('*remind', '').replace('*r', '').strip().split(" ")
            reason2 = message.replace('*remind', '').replace('*r', '').strip()
            reason3 = reason2.partition(' ')[2]
            remindeduser = reason0[0].lower()
            if remindeduser.startswith("@"):
                remindeduser = remindeduser[1:]
            remind_status[remindeduser] = {'remind': True}
            try:
                remind_status["reminders"][remindeduser].update({user: (user + " says: " + reason3 + " ")})
                sendmsg(currentchannel, '{} will be reminded : {}'.format(remindeduser, reason3))
                print(user + " did " + message + " in " + currentchannel)
            except:
                remind_status["reminders"][remindeduser] = {}
                remind_status["reminders"][remindeduser].update({user: (user + " says: " + reason3 + " ")})
                sendmsg(currentchannel, '{} will be reminded : {}'.format(remindeduser, reason3))
                print(user + " did " + message + " in " + currentchannel)

    if user in sleep_status:
        if sleep_status[user]['sleep']:
            sleep_status[user]['sleep'] = False
            timereply('{} is awake!  {} , {} {}, {} {}', user, messagetime, sleep_status, currentchannel)

    if message.startswith('*gn') or message.startswith('*goodnight'):
        if time.time() - timelast >= 3:
            timelast = time.time()
            reason = message.replace('*gn', '').replace('*goodnight', '').strip()
            sleep_status[user] = {'sleep': True, 'reason': reason}
            sendmsg(currentchannel, '{} is now asleep 🛌 💤 : {}'.format(user, reason))
            sleep_status[user]['time'] = messagetime
            print(user + " did " + message + " in " + currentchannel)

    if user in afk_status:
        if afk_status[user]['afk']:
            afk_status[user]['afk'] = False
            timereply('{} is back!  {} , {} {}, {} {}', user, messagetime, afk_status, currentchannel)

    if message.startswith('*afk') or message.startswith('*brb'):
        if time.time() - timelast >= 3:
            timelast = time.time()
            reason = message.replace('*afk', '').replace('*brb', '').strip()
            afk_status[user] = {'afk': True, 'reason': reason}
            sendmsg(currentchannel, '{} is now afk ⌨️ : {}'.format(user, reason))
            afk_status[user]['time'] = messagetime
            print(user + " did " + message + " in " + currentchannel)

    if message.startswith('*query'):
        reason = message.replace('*query', '').strip()
        sendmsg(currentchannel, wolfram(reason))

    if message.startswith('*tuck'):
        if time.time() - timelast >= 3:
            timelast = time.time()
            tuck0 = message.replace('*tuck', '').strip().split(" ")
            tucked = tuck0[0]
            tuck1 = tuck0[1:]
            global tuckemote
            try:
                tuck2 = tuck0[1]  # forces error
                tuckemote = " ".join(tuck1)
                message2 = '{} tucks {} into bed. {} 👉 🛏️ Good night! '.format(user, tucked, tuckemote)
                sendmsg(currentchannel, message2)
                print(user + " did " + message + " in " + currentchannel)
            except:
                message2 = '{} tucks {} into bed. 👉 🛏️ Good night! '.format(user, tucked)
                sendmsg(currentchannel, message2)
                print(user + " did " + message + " in " + currentchannel)

    if (message.startswith('*commands') or message.startswith('*help') or message.startswith('!help') or message.
            startswith('!commands')) and time.time() - timelast >= 3:
        timelast = time.time()
        sendmsg(currentchannel, "Current commands are * + tuck, afk, brb, ping, remind, r, goodnight, gn, cookie")
        print(user + " did " + message + " in " + currentchannel)
    if message.startswith('*cookie'):
        sendmsg(currentchannel, (random.choice(cookielist)))
        print(user + " did " + message + " in " + currentchannel)
    if message.startswith('*ping'):
        if time.time()-timelast >= 3:
            timelast = time.time()
            curtime = int((time.time() - startdate))
            ti = "seconds"
            if 60 < curtime < 3600:
                curtime = int(curtime / 60)
                ti = "minutes"
            if 3600 < curtime < 86400:
                curtime = int(curtime / 60 / 60)
                ti = "hours"
            if curtime > 86400:
                curtime = int(curtime / 60 / 60 / 24)
                ti = "days"
            sendmsg(currentchannel, "PONG! Uptime = {} {}".format(curtime, ti))
            print(user + " did " + message + " in " + currentchannel)



last_execution_time = datetime.datetime.now()

while True:
    while True:

        processed_ids = load_history()
        last_check_time = 0
        check_interval = 60  # Check every 10 minutes

        current_time3 = time.time()
        if current_time3 - last_check_time > check_interval:
            processed_ids = check_new_posts(reddit, subreddit_name, processed_ids)
            save_history(processed_ids)
            last_check_time = current_time3

        if time.time() - startTime > 5400: # Automatically shutdowns and saves
            afkfile = json.dumps(afk_status)
            sleepfile = json.dumps(sleep_status)
            timefile = json.dumps(time_status)
            remindfile = json.dumps(remind_status)
            afk = open('afkfileT.json', 'w')
            afk.write(afkfile)
            afk.close()
            sleep = open('sleepfileT.json', 'w')
            sleep.write(sleepfile)
            sleep.close()
            timey = open('timefileT.json', 'w')
            timey.write(timefile)
            timey.close()
            remind = open('remindfileT.json', 'w')
            remind.write(remindfile)
            remind.close()
            print("Shutting down.")
            exit()
        else:

            buffer += irc.recv(2048).decode("UTF-8", errors="ignore")
            split = buffer.split('\r\n')
            splitLen = len(split)
            if splitLen >= 2:
                for currentLine in split[:-1]:
                    processTwitchLine(currentLine)  # process each line
                buffer = split[-1]
