import os
import json
import requests
import threading

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


INIT_PATH: str = "/shared/init"
STATUS_PATH: str = "/shared/status"
MODULE_NAME: str = os.getenv("MODULE_NAME")


def write_uninit():
    with open(INIT_PATH, "w") as file:
        file.write("0")


def is_flying() -> bool:
    """ Проверка, что дрон не летает. """
    with open(STATUS_PATH, "a+") as file:
        pass

    with open(STATUS_PATH, "r") as file:
        status = file.read()

    if not status or status == "0":
        print("[EMERGENCY_DEBUG] drone is flying")
        return False

    print("[EMERGENCY_DEBUG] drone is landed")

    return True


def handle_event(id, details_str):
    """ Модуль сбора данных. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    write_uninit()
    if operation == "stop" and is_flying():
        write_uninit()

        proceed_to_deliver(id, {
            "deliver_to": "emergency-servos",
            "operation": "land"
        })

        write_uninit()


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
