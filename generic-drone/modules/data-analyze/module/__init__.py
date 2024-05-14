import os

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from multiprocessing import Queue

from .consumer import start_consumer
from .producer import start_producer


MODULE_NAME = os.getenv('MODULE_NAME')
INIT_PATH = "/shared/init"
STATE_PATH = "/shared/status"
COORDS_PATH = "/shared/coords"
BATTERY_PATH = "/shared/battery"


def main():
    print(f'[DEBUG] {MODULE_NAME} started...')

    with open(INIT_PATH, "w") as file:
        file.write("0")
    with open(STATE_PATH, "w") as file:
        file.write("0")
    with open(BATTERY_PATH, "w") as file:
        file.write("100")
    with open(COORDS_PATH, "w") as file:
        file.write("0,0,0")


    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser[MODULE_NAME])

    requests_queue = Queue()
    print(f'Running {MODULE_NAME}_consumer...')
    start_consumer(args, config)
    print(f'Running {MODULE_NAME}_producer...')
    start_producer(args, config, requests_queue)
