import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv("MODULE_NAME")


def send_ok(id, data):
    proceed_to_deliver(id, {
        "id": id,
        "source": MODULE_NAME,
        "deliver_to": "drone-data",
        "operation": "send_response",
        "data": data,
        "status": 200
    })


def send_error(id, data):
    proceed_to_deliver(id, {
        "id": id,
        "source": MODULE_NAME,
        "deliver_to": "drone-data",
        "operation": "send_error",
        "data": data,
        "status": 400
    })


def set_data(id, data):
    print("[MANAGER_DEBUG] Data from data-gruber:", data)

    coords = data.get("coords")
    battery = data.get("battery")

    if not all((coords, battery)):
        return


def send_data(id, data):
    print("[MANAGER_DEBUG] Encrypted telemetry:", data)


commands = {
    "set_data": set_data,
    "send_data": send_data
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

    if operation == "set_data":
        return set_data(id, data)

    if operation != "process_command":
        return

    command = commands.get(process_command)
    if command:
        command(id, data)


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
