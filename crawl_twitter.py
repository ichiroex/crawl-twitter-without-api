#!/usr/bin/env python3 # -*- coding: utf-8 -*-

# Author: mhiro2

"""
usage: crawl_twitter.py --word=<word> [--since=<since>] [--until=<until>]
       crawl_twitter.py --user=<user> [--since=<since>] [--until=<until>]
       crawl_twitter.py -h | --help

options:
    -h, --help  show this help message and exit
    --user=<user>      user name
    --since=<since>    since date [default: 2014-12-01]
    --until=<until>    until date [default: 2014-12-31]
"""

import csv
import json
import random
import requests
import sys
import time
from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime
from docopt import docopt

# Structure definition
User = namedtuple('User', ['user_id', 'user_name', 'user_screen_name'])
Tweet = namedtuple('Tweet', ['tweet_id', 'tweet', 'user', 'timestamp', 'retweets', 'favourites'])


class TweetSearcher(object):
    baseurl = 'https://twitter.com/i/search/timeline?'

    def __init__(self, query, wait_time=0, error_delay=5):
        self.query = query
        self.wait_time = wait_time
        self.error_delay = error_delay

    def run(self):
        payload = self.construct_payload()
        response = self.execute_search(payload)

        min_tweet_id = None
        result = []

        while response is not None and response['items_html'] is not None:
            tweets = self.parse_tweet(response['items_html'])

            if not tweets:
                break
            else:
                result.extend(tweets)

            if not min_tweet_id:
                min_tweet_id = tweets[0].tweet_id
#
            max_tweet_id = tweets[-1].tweet_id
#
            if min_tweet_id != max_tweet_id:
                max_position = 'TWEET-{0}-{1}'.format(max_tweet_id, min_tweet_id)
                payload = self.construct_payload(max_position=max_position)
                time.sleep(random.randint(0, self.wait_time))
                response = self.execute_search(payload)

        return result

    def construct_payload(self, max_position=None):
        payload = {
            'q': self.query,
            'f': 'tweets',
            'lang' : 'ja'
        }

        if max_position is not None:
            payload['max_position'] = max_position

        return payload

    def execute_search(self, payload):
        try:
            response = requests.get(TweetSearcher.baseurl, params=payload)
            data = json.loads(response.text, 'utf-8')
            return data

        except ValueError as e:
            print(e.message)
            print('Response Error!! wait {0} seconds'.format(self.error_delay),
                  file=sys.stderr)
            sleep(self.error_delay)
            return self.execute_search(url)

    @staticmethod
    def parse_tweet(html):
        soup = BeautifulSoup(html,  'lxml')
        tweet_list = []

        for li in soup.find_all('li', class_='js-stream-item'):
            if 'data-item-id' not in li.attrs:
                continue

            # tweet id
            tweet_id = li['data-item-id']
    
            # body text
            text = li.find('p', class_='js-tweet-text').text
    
            # timestamp
            unix_timestamp = li.find('span',class_='_timestamp')['data-time']
            timestamp = datetime.fromtimestamp(int(unix_timestamp))
    
            # user information
            user_tag = li.find('div', class_='tweet')
            user = User(user_tag['data-user-id'],
                        user_tag['data-name'],
                        user_tag['data-screen-name'])
    
            # retweets
            rt_tag = li.find('span', class_='ProfileTweet-action--retweet')
            rt = (rt_tag.find('span',class_='ProfileTweet-actionCount')
                  ['data-tweet-stat-count'])
    
            # favorites
            fv_tag = li.find('span', class_='ProfileTweet-action--favorite')
            fv = (fv_tag.find('span',class_='ProfileTweet-actionCount')
                  ['data-tweet-stat-count'])
    
            tweet = Tweet(tweet_id, text, user, timestamp, rt, fv)
            tweet_list.append(tweet)

        return tweet_list


def print_csv(tweets):
    field_names = ['tweet_id', 'tweet', 'user_id', 'user_name',
                   'user_screen_name', 'timestamp', 'retweets', 'favourites']

    writer = csv.DictWriter(sys.stdout, field_names, lineterminator='\n')
    writer.writeheader()

    for t in tweets[::-1]:
        attrs = vars(t)
        user_attrs = vars(attrs['user'])
        del attrs['user']
        attrs.update(user_attrs)
        writer.writerow(attrs)


def main():
    args = docopt(__doc__)

    word = args['--word']
    user = args['--user']
    since_date = args['--since']
    until_date = args['--until']

    # 'include:retweets' doesn't work now

    if word:
        query = '{0} since:{1} until:{2}'.format(word, since_date, until_date)
    elif user:
        query = 'from:{0} since:{1} until:{2}'.format(user, since_date, until_date)
    else:
        return

    searcher = TweetSearcher(query)
    result = searcher.run()

    if result:
        print_csv(result)


if __name__ == '__main__':
    main()
