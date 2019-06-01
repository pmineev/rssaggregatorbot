import logging
import time

import feedparser
import parse

log = logging.getLogger(__name__)


def bozo(feed):
    if feed['bozo']:
        log.warning(feed['bozo_exception'])


def get_nplus1():
    feed = feedparser.parse('https://nplus1.ru/rss')
    bozo(feed)
    feed_parsed = []
    for entry in feed.entries:
        post = dict()
        post['title'] = entry['title'].replace('&nbsp;', ' ')
        post['link'] = entry['link']
        post['summary'] = ''.join(entry['summary']).replace('&nbsp;', ' ')

        post['img_link'] = entry['media_content'][0]['url']
        if not post['img_link'].startswith('http'):
            post['img_link'] = None

        post['date'] = int(time.mktime(entry['published_parsed']))
        post['category'] = None

        feed_parsed.append(post)

    return feed_parsed


def get_postnauka():
    feed = feedparser.parse('https://postnauka.ru/feed')
    bozo(feed)
    feed_parsed = []
    for entry in feed.entries:
        post = dict()
        post['title'] = entry['title']
        post['link'] = entry['link']

        summary_parsed = parse.parse('<img src="{}"><div>{}</div>', entry['summary'])
        post['summary'] = summary_parsed[1]
        post['img_link'] = summary_parsed[0]

        post['date'] = int(time.mktime(entry['published_parsed']))
        post['category'] = None

        feed_parsed.append(post)

    return feed_parsed


def get_meduza():
    # для карточек
    def summary_cards(text):
        lines = text.split('</li><li>')
        lines[0] = lines[0].replace('<ol><li>', '1. ')
        lines[-1] = lines[-1].replace('</li></ol>', '')
        q = ''.join([lines[0]] + ["\n" + str(i) + '. ' + s for i, s in enumerate(lines[1:], 2)])
        return q

    feed = feedparser.parse('https://meduza.io/rss/all')
    bozo(feed)
    feed_parsed = []
    for entry in feed.entries:
        post = dict()
        post['title'] = entry['title'].replace('\xa0', ' ')
        post['link'] = entry['link']

        post['summary'] = entry['summary'].replace('\xa0', ' ')
        if post['summary'].startswith('<ol><li>'):
            post['summary'] = summary_cards(post['summary'])

        post['img_link'] = entry['links'][1]['href']
        post['date'] = int(time.mktime(entry['published_parsed']))
        post['category'] = None

        feed_parsed.append(post)

    return feed_parsed


def get_lenta():
    feed = feedparser.parse('https://lenta.ru/rss')
    bozo(feed)
    feed_parsed = []
    for entry in feed.entries:
        post = dict()
        post['title'] = entry['title']
        post['link'] = entry['link']

        post['summary'] = entry['summary']
        post['img_link'] = entry['links'][1]['href']

        post['date'] = int(time.mktime(entry['published_parsed']))
        post['category'] = entry['tags'][0]['term'] if 'tags' in entry else None

        feed_parsed.append(post)

    return feed_parsed


sources = {'nplus1': get_nplus1,
           'postnauka': get_postnauka,
           'meduza': get_meduza,
           'lenta': get_lenta}
