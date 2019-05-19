import logging

from rssbot import RssBot

logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='{asctime}|{levelname:<8}|{name:<10}|{message}',
                    datefmt='%H:%M:%S')

log = logging.getLogger(__name__)


def main():
    RssBot()


if __name__ == '__main__':
    main()
