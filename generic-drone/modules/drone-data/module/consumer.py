import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")
PSSWD_PATH: str = "/module/config/psswd"
TOKEN_PATH: str = "/module/config/token"
NAME_PATH: str = "/module/config/name"
HASH_PATH: str = "/module/config/hash"
COORDS_PATH: str = "/shared/coords"
ATM_URL: str = "http://atm:6064"


def set_password(id, details):
    """ Сохраняет полученный от авторизации пароль """
    print("[DEF_STORAGE_DEBUG] Password set to", details.get("psswd"))
    print("[DEF_STORAGE_DEBUG] Name set to", details.get("name"))

    with open(PSSWD_PATH, "w") as file:
        file.write(details.get("psswd"))

    with open(NAME_PATH, "w") as file:
        file.write(details.get("name"))


def set_token(id, details):
    print("[DEF_STORAGE_DEBUG] Token set to", details.get("token"))
    with open(TOKEN_PATH, "w") as file:
        file.write(details.get("token"))


def set_hash(id, details):
    print("[DEF_STORAGE_DEBUG] Hash set to", details.get("hash"))
    with open(HASH_PATH, "w") as file:
        file.write(details.get("hash"))


def get_name():
    with open(NAME_PATH, "r") as file:
        return file.read()


def send_response(id, details):
    proceed_to_deliver(id, {
        "deliver_to": "chipher",
        "operation": "send_response",
        "data": details["data"],
        "status": 200
    })


def send_error(id, details):
    proceed_to_deliver(id, {
        "deliver_to": "chipher",
        "operation": "send_error",
        "data": details["data"],
        "status": 400
    })


def register(id, details):
    proceed_to_deliver(id, {
        "name": get_name(),
        "deliver_to": "chipher",
        "data": details.get("data"),
        "operation": "regiser"
    })


commands = {
    "set_password": set_password,
    "set_token": set_token,
    "set_hash": set_hash,
    "send_response": send_response,
    "send_error": send_error,
    "register": register
}


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    # Выполнение нужной команды
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
