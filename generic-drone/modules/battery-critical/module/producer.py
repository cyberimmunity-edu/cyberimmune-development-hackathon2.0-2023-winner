import os
import json
import threading
import multiprocessing

from uuid import uuid4
from time import sleep
from confluent_kafka import Producer


_requests_queue: multiprocessing.Queue = None
MODULE_NAME = os.getenv("MODULE_NAME")
INIT_PATH: str = "/shared/init"
BATTERY_PATH: str = "/shared/battery"

def low_power(battery):
    print("[BATTERY_DEBUG] Low power:", battery)

    return proceed_to_deliver(uuid4().__str__(), {
        "deliver_to": "data-gruber",
        "operation": "low_power",
        "battery": battery
    })


def read_init():
    with open(INIT_PATH, "a+") as file:
        pass

    with open(INIT_PATH, "r") as file:
        return file.read() == "1"


def write_battery(battery: int):
    with open(BATTERY_PATH, "w") as file:
        file.write(str(battery))


def get_battery() -> int:
    while True:
        if not read_init():
            sleep(10)
            continue

        with open(BATTERY_PATH, "a+") as file:
            pass

        with open(BATTERY_PATH, "r") as file:
            battery = file.read()

        print("[BATTERY_DEBUG] Readed battery:", battery)

        if not battery.isnumeric():
            print("[BATTERY_DEBUG] Readed battery is not a num")
            write_battery(0)
            low_power(0)
            continue

        battery = int(battery)
        if battery > 100:
            write_battery(100)
            battery = 100

        print("[BATTERY_DEBUG] Battery:", battery)
        if battery < 20:
            low_power(battery)

        sleep(10)


def proceed_to_deliver(id, details):
    details["source"] = MODULE_NAME
    details["id"] = id
    _requests_queue.put(details)


def producer_job(_, config, requests_queue: multiprocessing.Queue):
    producer = Producer(config)

    def delivery_callback(err, msg):
        if err:
            print("[error] Message failed delivery: {}".format(err))

    threading.Thread(target=get_battery).start()

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
