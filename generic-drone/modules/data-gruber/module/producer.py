import os
import json
import threading
import multiprocessing

from uuid import uuid4
from time import sleep
from confluent_kafka import Producer


_requests_queue: multiprocessing.Queue = None
MODULE_NAME = os.getenv("MODULE_NAME")
INIT_PATH = "/shared/init"


def proceed_to_deliver(id, details):
    details["id"] = id
    details["source"] = MODULE_NAME
    _requests_queue.put(details)


def read_init():
    with open(INIT_PATH, "a+") as file:
        pass

    with open(INIT_PATH, "r") as file:
        return file.read() == "1"


def health_check():
    while True:
        if not read_init():
            sleep(5)
            continue

        proceed_to_deliver(uuid4().__str__(), {
            "deliver_to": "health-check",
            "operation": "check"
        })

        sleep(5)


def producer_job(_, config, requests_queue: multiprocessing.Queue):
    producer = Producer(config)

    def delivery_callback(err, msg):
        if err:
            print("[error] Message failed delivery: {}".format(err))

    threading.Thread(target=health_check).start()

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
