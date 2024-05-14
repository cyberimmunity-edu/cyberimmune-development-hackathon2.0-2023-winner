import os
import json
import requests
import threading

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


STATUS_PATH: str = "/shared/status"
MODULE_NAME: str = os.getenv("MODULE_NAME")

config = {}
retries = 0
retries_coords = 0


def is_flying():
    with open(STATUS_PATH, "a+") as file:
        pass
    with open(STATUS_PATH, "r") as file:
        return file.read() == "1"


def send_emergency(id):
    """ Запроса аварийной посадки. """
    print("[DATA_GRUBER_DEBUG] Send emergency!")
    proceed_to_deliver(id, {
        "deliver_to": "emergency",
        "operation": "stop"
    })


def send_data(id, data):
    """ Обработка и отправка данных. """
    print("[DATA_GRUBER_DEBUG] Config:", data)

    global retries

    if not all((data.get("coords"), data.get("battery"))):
        print("[DATA_GRUBER_DEBUG] One system skipped!")
        retries += 1

    # Если в течении 3 раз нам что-то не пришло
    if retries > 3:
        print("[DATA_GRUBER_DEBUG] System ERROR!")
        retries = 0
        return send_emergency(id)

    # Если мы получили координаты и заряд, то отправляем дальше
    if all((data.get("coords"), data.get("battery"))):
        retries = 0

        print("[DATA_GRUBER_DEBUG] Send system data:", data)
        proceed_to_deliver(id, {
            "deliver_to": "manager",
            "operation": "set_data",
            "data": data
        })


def set_coords(id, details):
    """ Получение данных из комплексирования. """

    global config
    global retries_coords

    print("[DATA_GRUBER_DEBUG] New coords:", details["coords"])

    # Перестали приходить данные от навигационной системы
    if config.get("coords") == details["coords"]:
        print("[DATA_GRUBER_DEBUG] Prob nvigation fail?")
        retries_coords += 1

    if retries > 6 and is_flying():
        print("[DATA_GRUBER_DEBUG] Navigation ERROR!")
        retries_coords = 0
        return send_emergency(id)

    if config.get("coords") != details["coords"]:
        retries_coords = 0

    config["coords"] = details["coords"]
    send_data(id, config)


def set_battery(id, details):
    """ Получение данных из самодиагностики. """
    global config

    config["battery"] = details["battery"]
    if details["battery"] < 20:
        print("[DATA_GRUBER_DEBUG] LOW POWER!")
        return send_emergency(id)

    send_data(id, config)


def low_power(id, details):
    """ Получение данных из модуля критичного заряда батареи. """
    global config

    print("[DATA_GRUBER_DEBUG] LOW POWER!")

    config["battery"] = details["battery"]
    send_emergency(id)


commands = {
    "set_coords": set_coords,
    "set_battery": set_battery,
    "low_power": low_power
}


def handle_event(id, details_str):
    """ Модуль сбора данных. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    command = commands.get(operation)
    if command:
        command(id, details)


def consumer_job(args, config):
    consumer = Consumer(config)

    def reset_offset(verifier_consumer, partitions):
        if not args.reset:
            return

        for p in partitions:
            p.offset = OFFSET_BEGINNING
        verifier_consumer.assign(partitions)

    topic = MODULE_NAME
    consumer.subscribe([topic], on_assign=reset_offset)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    id = msg.key().decode('utf-8')
                    details_str = msg.value().decode('utf-8')
                    handle_event(id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event received from " \
                          f"topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()

def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()
    threading.Thread(target=lambda: consumer_job(args, config)).start()
