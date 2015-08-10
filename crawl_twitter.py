#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import requests
import time
from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime
from docopt import docopt

# Structure definition
User = namedtuple('User', ['user_id', 'user_name', 'user_screen_name'])
Tweet = namedtuple('Tweet', ['tweet_id', 'tweet', 'user', 'timestamp', 'retweets', 'favourites'])
Response = namedtuple('Response', ['has_more_items', 'items_html'])


class TweetSearcher(object):
    baseurl = 'https://twitter.com/i/search/timeline?'

    def __init__(self, query):
        self.query = query
        self.maxtweet = None
        self.mintweet = None

    def run(self):
        payload = {
            'q': self.query,
            'f': 'tweets',
            'include_available_features': 1,
            'include_entities': 1,
            'last_note_ts': int(time.time()),
            'src' : 'typd'
        }
        raw = requests.get(TweetSearcher.baseurl, params=payload)
        js = json.loads(raw.text, 'utf-8')
        response = Response(js['has_more_items'], js['items_html'])

        soup = BeautifulSoup(response.items_html, 'lxml')
        result = parse_tweet(soup)

        if result:
            self.mintweet = result[0].tweet_id
            self.maxtweet = result[-1].tweet_id

        while response.has_more_items:
            if self.mintweet == self.maxtweet:
                break
            max_position = 'TWEET-{0}-{1}'.format(self.maxtweet, self.mintweet)

            response = self.tweet_search_previous(max_position)
            soup = BeautifulSoup(response.items_html, 'lxml')
            current_result = parse_tweet(soup)

            result.extend(current_result)
            self.mintweet = current_result[0].tweet_id
            self.maxtweet = current_result[-1].tweet_id

        return result

    def tweet_search_previous(self, max_position):
        payload = {
            'q': self.query,
            'f': 'tweets',
            'include_available_features': 1,
            'include_entities': 1,
            'last_note_ts': int(time.time()),
            'max_position': max_position,
            'src' : 'typd'
        }
        raw = requests.get(TweetSearcher.baseurl, params=payload)
        js = json.loads(raw.text, 'utf-8')
        return Response(js['has_more_items'], js['items_html'])


def parse_tweet(soup):
    results = []
    try:
        for t in soup.find_all('li', class_='js-stream-item'):
            # tweet id
            tweet_id = t['data-item-id']

            # body text
            text = t.find('p', class_='js-tweet-text').text

            # timestamp
            unix_timestamp = t.find('span',class_='_timestamp')['data-time']
            timestamp = datetime.fromtimestamp(int(unix_timestamp))

            # user information
            user_tag = t.find('div', class_='tweet')
            user = User(user_tag['data-user-id'],
                        user_tag['data-name'],
                        user_tag['data-screen-name'])

            # retweets
            rt_tag = t.find('span', class_='ProfileTweet-action--retweet')
            rt = (rt_tag.find('span',class_='ProfileTweet-actionCount')
                  ['data-tweet-stat-count'])

            # favorites
            fv_tag = t.find('span', class_='ProfileTweet-action--favorite')
            fv = (fv_tag.find('span',class_='ProfileTweet-actionCount')
                  ['data-tweet-stat-count'])

            tweet = Tweet(tweet_id, text, user, timestamp, rt, fv)
            results.append(tweet)
    except KeyError:
        pass

    return results


def write_csv(tweets, filename):
    field_names = ['tweet_id', 'tweet', 'user_id', 'user_name',
                   'user_screen_name', 'timestamp', 'retweets', 'favourites']

    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, field_names, lineterminator='\n')
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
        output_file = '{0}.csv'.format(word)
    elif user:
        query = 'from:{0} since:{1} until:{2}'.format(user, since_date, until_date)
        output_file = '{0}.csv'.format(user)
    else:
        return

    searcher = TweetSearcher(query)
    result = searcher.run()
    write_csv(result, output_file)


if __name__ == '__main__':
    main()
