import os
import json
import threading

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


# Константы
MODULE_NAME: str = os.getenv("MODULE_NAME")
BATTERY_PATH: str = "/shared/battery"
COORDS_PATH: str = "/shared/coords"
# Под статусом подразумевается "летает" (1 в файле) или "приземлён" (0)
STATUS_PATH: str = "/shared/coords"
# Подразумевается, что датчики не отправляют информацию,
# пока дрон не инициализирован
INIT_PATH: str = "/shared/init"


def send_fps_response(id, data):
    return proceed_to_deliver(id,{
        "deliver_to": "manager",
        "operation": "send_fps_response",
        "data": data
    })


def send_fps_error(id, data):
    return proceed_to_deliver(id,{
        "deliver_to": "manager",
        "operation": "send_fps_error",
        "data": data
    })


def write_coordinates(coordinates):
    """
        Записывает положение дрона.

        Требуется для имитации навигации
    """

    print("[DATA_ANALYZE_DEBUG] Initiate coordinates:", coordinates)

    with open(COORDS_PATH, "w") as file:
        file.write(",".join(map(str, coordinates)))


def write_battery(battery: int):
    """
        Записывает заряд аккумулятора дрона.

        Требуется для имитации работы аккумулятора
    """

    print("[DATA_ANALYZE_DEBUG] Initiate battery:", battery)

    with open(BATTERY_PATH, "w") as file:
        # Изначально дрон приземлён
        file.write(str(battery))


def write_status():
    """
        Записывает статус полёта дрона.

        0 - статус "приземления"
        1 - статус "полёта"

        Требуется для имитации работы аварийной системы
    """

    print("[DATA_ANALYZE_DEBUG] Initiate status: 0")

    with open(BATTERY_PATH, "w") as file:
        # Изначально дрон приземлён
        file.write("0")


def write_init():
    """
        Записывает статус инициализации дрона.

        0 - статус "неинициализирован"
        1 - статус "инициализирован"

        Требуется для имитации работы датчиков
    """

    print("[DATA_ANALYZE_DEBUG] Initiate init: 1")

    with open(INIT_PATH, "w") as file:
        # Изначально дрон приземлён
        file.write("1")


def initiate_drone(id, details):
    """ Инициализация дрона. """

    print("[DATA_ANALYZE_DEBUG] Initiate command")

    name = details["name"]
    psswd = details["psswd"]
    coordinate = details["data"]["coordinate"]

    # Сохраняем данные для имитации работы модулуй
    write_init()
    write_status()
    write_battery(100)
    write_coordinates(coordinate)

    # Отдаём модулю данных дрона креды
    proceed_to_deliver(uuid4().__str__(), {
        "deliver_to": "drone-data",
        "operation": "set_password",
        "name": name,
        "psswd": psswd
    })

    proceed_to_deliver(id, {
        "id": id,
        "deliver_to": "drone-data",
        "operation": "send_response",
        "data": {"msg": f"drone init at {coordinate}"}
    })


def register_drone(id, details):
    """
        Процесс регистрации дрона, запущенный системой
        планирования полётов.
    """

    print("[DATA_ANALYZE_DEBUG] Register drone...")

    proceed_to_deliver(id, {
        "id": id,
        "source": MODULE_NAME,
        "deliver_to": "drone-data",
        "operation": "register",
        "data": details["data"]
    })


def set_token(id, details):
    token = details["token"]
    print("[DATA_ANALYZE_DEBUG] Set token:", token)

    # Отдаём модулю данных дрона креды
    proceed_to_deliver(uuid4().__str__(), {
        "deliver_to": "drone-data",
        "operation": "set_token",
        "token": token
    })


def task_status_change(id, details):
    drone_hash = details["hash"]
    print("[DATA_ANALYZE_DEBUG] Set hash:", drone_hash)

    # Отдаём модулю данных дрона креды
    proceed_to_deliver(uuid4().__str__(), {
        "deliver_to": "drone-data",
        "operation": "set_hash",
        "hash": drone_hash
    })


def emergency(id, details):
    """
        Процесс аварийной остановки дрона, запущенный системой
        организации воздушного движения.
    """

    print("[DATA_ANALYZE_DEBUG] Stop Drone Emergency...")
    proceed_to_deliver(id, {
        "deliver_to": "emergency",
        "operation": "stop"
    })


def start(id, details):
    print("[DATA_ANALYZE_DEBUG] Start drone...")


def stop(id, details):
    print("[DATA_ANALYZE_DEBUG] Stop drone...")


def sign_out(id, details):
    print("[DATA_ANALYZE_DEBUG] Sign out drone...")


def clear_flag(id, details):
    print("[DATA_ANALYZE_DEBUG] Clear emergency drone...")


def set_task(id, details):
    print("[DATA_ANALYZE_DEBUG] Set task drone...")


commands = {
    "set_token": set_token,
    "task_status_change": task_status_change,
    "start": start,
    "stop": stop,
    "sign_out": sign_out,
    "clear_flag": clear_flag,
    "set_task": set_task

}


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """

    details = json.loads(details_str)

    data: str = details.get("data")
    source: str = details.get("source")
    operation: str = details.get("operation")
    deliver_to: str = details.get("deliver_to")
    process_command: str = details.get("process_command")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    print("[DATA_ANALYZE_DEBUG] New task:", details)

    if operation != "process_command":
        return

    if process_command == "emergency":
        return emergency(id, details)
    elif process_command == "initiate":
        return initiate_drone(id, details)
    elif process_command == "register":
        return register_drone(id, details)

    command = commands.get(process_command)
    if not command:
        return

    command(id, details)
    proceed_to_deliver(id, {
        "deliver_to": "manager",
        "operation": "process_command",
        "process_command": process_command,
        "data": details["data"]
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
