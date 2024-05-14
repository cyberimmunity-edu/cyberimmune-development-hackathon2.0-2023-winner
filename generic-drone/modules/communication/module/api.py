import os
import time
import json
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


# Константы
HOST: str = "0.0.0.0"
PORT: int = int(os.getenv("MODULE_PORT"))
MODULE_NAME: str = os.getenv("MODULE_NAME")
MAX_WAIT_TIME: int = 10
ATM_URL: str = "http://atm:6064"
FPS_URL: str = "http://fps:6065"
CONTENT_HEADER = {"Content-Type": "application/json"}


# Очереди задач и ответов
_requests_queue: multiprocessing.Queue = None
_response_queue: multiprocessing.Queue = None


app = Flask(__name__)


def send_to_authenticator(details):
    """ Отправляет задачу на проверку аутентичности. """
    if not details:
        abort(400)

    details["deliver_to"] = "chipher"
    details["source"] = MODULE_NAME
    details["id"] = uuid4().__str__()

    try:
        _requests_queue.put(details)
        print(f"{MODULE_NAME} update event: {details}")
    except Exception as e:
        print("[COMMUNICATION_DEBUG] malformed request", e)
        abort(400)


def wait_response():
    """ Ожидает завершение выполнения задачи. """
    start_time = time.time()
    while 1:
        if time.time() - start_time > MAX_WAIT_TIME:
            break

        try:
            response = _response_queue.get(timeout=MAX_WAIT_TIME)
        except Exception as e:
            print("[COMMUNICATION_DEBUG] timeout...", e)
            continue

        if not isinstance(response, dict):
            print("[COMMUNICATION_DEBUG] not a dict...")
            continue

        data = response.get('data')
        if response.get('deliver_to') != 'communication' or not data:
            print("[COMMUNICATION_DEBUG] something strange...")
            continue

        print("[COMMUNICATION_DEBUG] response", response)
        return data

    print("[COMMUNICATION_DEBUG] OUT OF TIME...")

    return None


@app.post("/set_command")
def set_command():
    """
        Принимает входящую команду и передаёт
        модулю проверки аутентичности.
    """
    try:
        content = request.json
    except Exception as e:
        print("[COMMUNICATION_ERROR]", e)
        abort(400)

    print(f'[COMMUNICATION_DEBUG] received {content}')

    details_to_send = {
        "operation": content.get("command"),
        "data": content,
    }

    send_to_authenticator(details_to_send)
    data = wait_response()
    if not data:
        abort(400)

    return data


# Обработчик ошибок
@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web(requests_queue, response_queue):
    global _requests_queue
    global _response_queue

    _requests_queue = requests_queue
    _response_queue = response_queue

    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()
