import os
import json
import threading
import multiprocessing

from uuid import uuid4
from time import sleep
from random import randint
from confluent_kafka import Producer

_requests_queue: multiprocessing.Queue = None
INIT_PATH: str = "/shared/init"
COORDS_PATH: str = "/shared/coords"
MODULE_NAME: str = os.getenv("MODULE_NAME")


def read_coords(error):
    """ Получает данные навигационной системы. """
    with open(COORDS_PATH, "a+") as file:
        pass

    with open(COORDS_PATH, "r") as file:
        coords = file.read().strip().split(",")

    if not coords or len(coords) != 3:
        return error

    try:
        coords = list(map(int, coords))
    except:
        return error

    print("[INS_DEBUG] Readed coords:", coords)

    return [coords[i] + error[i] for i in range(3)]


def read_init() -> bool:
    with open(INIT_PATH, "a+") as file:
        pass

    with open(INIT_PATH, "r") as file:
        status = file.read()

    return status == "1"


def generate_coordinates():
    """ Имитирует поведение навигационного блока. """
    while True:
        if not read_init():
            sleep(randint(5, 10))
            continue

        new_x: int = randint(-1, 1)
        new_y: int = randint(-1, 1)
        new_z: int = randint(-1, 1)

        coords = read_coords((new_x, new_y, new_z))

        print("[INS_DEBUG] Coords:", coords)

        proceed_to_deliver(uuid4().__str__(), {
            "deliver_to": "nav",
            "operation": "set_ins_coords",
            "coords": coords
        })

        sleep(randint(5, 10))


def proceed_to_deliver(id, details):
    details["id"] = id
    details["source"] = MODULE_NAME
    _requests_queue.put(details)


def producer_job(_, config, requests_queue: multiprocessing.Queue):
    producer = Producer(config)

    threading.Thread(target=generate_coordinates).start()

    def delivery_callback(err, msg):
        if err:
            print("[error] Message failed delivery: {}".format(err))

    topic = "monitor"
    while True:
        event_details = requests_queue.get()
        producer.produce(
            topic,
            json.dumps(event_details),
            event_details["id"],
            callback=delivery_callback
        )

        producer.poll(10000)
        producer.flush()


def start_producer(args, config, requests_queue):
    print(f"{MODULE_NAME}_producer started")

    global _requests_queue

    _requests_queue = requests_queue
    threading.Thread(
        target=lambda: producer_job(args, config, requests_queue)
    ).start()
