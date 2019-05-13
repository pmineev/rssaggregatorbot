from setuptools import setup

setup(
    name='rssaggregatorbot',
    version='1.0',
    packages=['python-telegram-bot', 'parse', 'feedparser', 'psycopg2'],
    author='Pavel Mineev',
    description='RSS aggregator bot for Telegram'
    )
