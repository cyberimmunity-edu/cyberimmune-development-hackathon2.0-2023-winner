import os
import json
import requests
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv("MODULE_NAME")
COORDS_PATH: str = "/shared/coords"
ATM_URL: str = "http://atm:6064"


def read_coords():
    """ Получает данные навигационной системы. """
    with open(COORDS_PATH, "a+") as file:
        pass

    with open(COORDS_PATH, "r") as file:
        coords = file.read().strip().split(",")

    if not coords or len(coords) != 3:
        return [0, 0, 0]

    try:
        coords = list(map(int, coords))
    except:
        return [0, 0, 0]

    return coords


def send_error(id, details):
    details["deliver_to"] = "communication"
    proceed_to_deliver(id, details)


def send_response(id, details):
    details["deliver_to"] = "communication"
    proceed_to_deliver(id, details)


def register(id, details):
    coords = read_coords()

    requests.post(f"{ATM_URL}/sign_up", json={
        "name": details["name"],
        "coordinate": coords,
        "status": "OK",
        "host": "communication",
        "port": "6066"
    })

    proceed_to_deliver(id, {
        "deliver_to": "communication",
        "operation": "send_response",
        "status": 200,
        "data": {"msg": "drone has been registered!"}
    })


commands = {
    "register": register,
    "send_error": send_error,
    "send_response": send_response,
}


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: str = details.get("data")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    command = commands.get(operation)
    if command:
        return command(id, details)

    if not data or not isinstance(data, dict):
        return

    # Возможные команды и поля данных для имитации расшифровки
    policies = {
        "initiate": ("name", "command", "coordinate", "psswd"),
        "start": ("name", "command", "psswd", "speed"),
        "stop": ("name", "command", "psswd"),
        "sign_out": ("name", "command", "psswd"),
        "new_task": ("name", "points"),
        "register": ("name", "command", "psswd"),
        "clear_flag": ("name", "command", "psswd"),
        "set_task": ("name", "points", "command", "psswd"),
        "emergency": ("name", "token"),
        "set_token": ("name", "command", "token"),
        "task_status_change": ("name", "command", "task_status",
                               "token", "hash"),
    }

    # Имитация расшифровки данных
    policy = policies.get(operation)
    if not policy or len(policy)  != len(data):
        print("[CHIPHER_DEBUG] Error while data decryption")
        return

    if set(policy) != set(data):
        print("[AUTHENTICATOR_DEBUG] Error while data decryption")
        return

    print("[CHIPHER_DEBUG] Successful data decryption")
    print("[CHIPHER_DEBUG] Decrypted data:", data)

    name = data.pop("name", None)
    psswd = data.pop("psswd", None)
    token = data.pop("token", None)

    return proceed_to_deliver(id, {
        "deliver_to": "data-analyze",
        "operation": "process_command",
        "process_command": operation,
        "data": data,
        "name": name,
        "psswd": psswd,
        "token": token,
    })


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
                    id = msg.key().decode("utf-8")
                    details_str = msg.value().decode("utf-8")
                    handle_event(id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event received from " \
                          f"topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()

def start_consumer(args, config):
    print(f"{MODULE_NAME}_consumer started")
    threading.Thread(target=lambda: consumer_job(args, config)).start()
