import os
import json
import requests
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")
ATM_URL: str = os.getenv("ATM_URL", "http://atm:6064")


def atm_sign_up(data):
    """
        Отправляет запрос на регистрацию
        в системе организации воздушного движения.
    """
    url = f"{ATM_URL}/sign_up"
    print("[SEND_ATM_DEBUG] SignUp in atm", url, "with", data)


def atm_sign_out(data):
    """
        Отправляет статус завершения маршрута
        в систему организации воздушного движения.
    """
    url = f"{ATM_URL}/sign_out"
    print("[SEND_ATM_DEBUG] SignOut in atm", url, "with", data)


def atm_watchdog(data):
    """ Отправляет запросы к системе организации воздушного движения. """
    url = f"{ATM_URL}/watchdog"
    print("[SEND_ATM_DEBUG] Watchdog in atm", url, "with", data)


def atm_data_in(data):
    """
        Отправляет данные
        в систему организации воздушного движения.
    """
    url = f"{ATM_URL}/data_in"
    print("[SEND_ATM_DEBUG] Send data to atm", url, "with", data)


commands = {
    "atm_sign_up": atm_sign_up,
    "atm_sign_out": atm_sign_out,
    "atm_watchdog": atm_watchdog,
    "atm_data_in": atm_data_in
}


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    # Выбор подходящей функции
    command = commands.get(operation)
    if command:
        command(details["data"])


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
