import configparser
import os
import sys
import random
from video_tweet import VideoTweet
from datetime import date, time, datetime, timedelta
import time as t

def upload_tweet(path):
    videoTweet = VideoTweet(path)
    videoTweet.upload_init()
    videoTweet.upload_append()
    videoTweet.upload_finalize()
    return videoTweet.tweet()

def generate_upload_times_for_today(num_gifs):
    start_time = datetime.combine(datetime.today(), time.fromisoformat('08:00:00'))
    if datetime.now() > start_time:
        start_time = datetime.now()
    end_time = datetime.combine(datetime.today(), time.fromisoformat('22:00:00'))
    if datetime.now() > end_time:
        return []
    delta = end_time - start_time
    times = []
    for i in range(num_gifs):
        times.append(start_time + (delta / num_gifs) * i)

    delta_minutes = (delta / num_gifs) // timedelta(minutes=1)
    print(delta_minutes)
    for i in range(len(times)):
        times[i] = times[i] + timedelta(minutes=random.randint(-delta_minutes//2, delta_minutes//2))
    return sorted(times) #just in case

config = configparser.ConfigParser()
config.read('config.ini')
img_path = config['DEFAULT']['path']
file_list = sorted(os.listdir(img_path))
log_file = config['DEFAULT']['log_file']

start_index = 0
if len(sys.argv) > 1:
    try:
        start_index = int(sys.argv[1])
    except:
        print("Usage: python upload_nightmare.py [start index]")
        exit(1)

next_upload = start_index

today = date.today()
halloween = date(today.year, 10, 31)
christmas = date(today.year, 12, 25)

if today < halloween or today > christmas:
    print("Nightmares can only be uploaded between Halloween and Christmas")
    exit(1)

days_until_christmas = (christmas-today).days
gifs_per_day = (len(file_list) - start_index) // days_until_christmas

while(next_upload <= len(file_list)):
    today = date.today()
    upload_times = generate_upload_times_for_today(gifs_per_day)
    for upload_time in upload_times:
        print("Waiting until {}".format(upload_time))
        while datetime.now() < upload_time:
            t.sleep(60)

        gif_to_upload = os.path.join(img_path, file_list[next_upload])
        if not upload_tweet(gif_to_upload):
            print("Tweet failed")
            exit(1)
        else:
            with open(log_file, 'a+') as f:
                print("Uploaded {}".format(gif_to_upload), file=f)
            next_upload = next_upload+1
    print("See you tomorrow")
    while today == date.today():
        t.sleep(7200)
        



