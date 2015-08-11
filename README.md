crawl-twitter-without-api
====

Twitter crawling script without official API

Requirements
---
    $ pip3 install -r requirements.txt

    $ pip3 freeze
    beautifulsoup4 (4.3.2)
    docopt (0.6.2)
    lxml (3.4.4)
    requests (2.7.0)

- I recommend that you use [pyenv](https://github.com/yyuu/pyenv) and Anaconda3

Usage
---
    $ python3 crawl_twitter.py --word="hoge" --since=2015-01-01 --until=2015-01-10
    $ python3 crawl_twitter.py --user=hoge --since=2015-01-01 --until=2015-01-10
