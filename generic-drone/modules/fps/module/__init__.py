#!/usr/bin/env python

import requests
import json
from random import randrange
from flask import Flask, request, jsonify


CONTENT_HEADER = {"Content-Type": "application/json"}
ATM_ENDPOINT_URI = "http://atm:6064/new_task"


drones = []


host_name = "0.0.0.0"
port = 6065
app = Flask(__name__)


class Drone:
    """ Класс дрона. """
    def __init__(
        self,
        coordinate,
        name: str,
        psswd: str,
        host: str,
        port: int
    ):
        self.coordinate = coordinate
        self.name = name
        self.psswd = psswd
        self.status = "Initiated"
        self.endpoint = f"http://{host}:{port}/set_command"


def return_error(request):
    """ Возвращает ошибку при неправильных входных данных. """
    error_message = f"malformed request {request.data}\n"
    return error_message, 400


def send_request(drone, data):
    try:
        response = requests.post(
            drone.endpoint,
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        ).json()
    except Exception as e:
        return f"Can't ping {drone.endpoint}\n"

    return jsonify(response), response.get('code', 400)


def log_drone(drone, cmd):
    " Выводит отладочную информацию для дрона. "
    print("[FPS_DEBUG] Using drone", drone.endpoint)
    print("[FPS_DEBUG] DRONE COMMAND:", cmd)
    print("[FPS_DEBUG] DRONE STATUS:", drone.status)
    print("[FPS_DEBUG] DRONE COORDINATE:", drone.coordinate)
    print("[FPS_DEBUG] DRONE NAME:", drone.name)
    print("[FPS_DEBUG] DRONE PSSWD:", drone.psswd)


@app.route("/set_command", methods=['POST'])
def set_command():
    try:
        content = request.json
    except Exception as e:
        return return_error(request)

    print(f'[FPS_DEBUG] received {content}')

    global drones

    # Получение параметров
    cmd = content.get('command')
    name = content.get('name')
    psswd = content.get('psswd')

    # Инициализация первого свободного дрона
    if cmd == 'initiate':
        coordinate = content.get('coordinate')

        drone = None
        for i in range(len(drones)):
            if drones[i].status != "Initiated":
                continue

            # Обновляем информацию о дроне
            drones[i].status = "Working"
            drones[i].coordinate = coordinate
            drones[i].psswd = psswd
            drones[i].name = name

            drone = drones[i]

            break

        # Свободного дрона не найдено
        if not drone:
            print("[FPS_INITIATE_ERROR] Not enough drones for this task")
            return return_error(request)

        log_drone(drone, cmd)

        data = {
            "name": name,
            "command": cmd,
            "coordinate": coordinate,
            "psswd": psswd
        }

        return send_request(drone, data)

    # Поиск дрона с заданным именем
    drone_tuple = tuple(filter(lambda i: name == i.name, drones))
    if len(drone_tuple) != 1:
        print("[FPS_SET_COMMAND_ERROR] Nonunique or unknown name:", name)
        return return_error(request)

    drone = drone_tuple[0]
    log_drone(drone, cmd)

    data = {}

    # Запуск дрона
    if cmd == "start":
        speed = content.get('speed')

        data = {
            "name": name,
            "command": cmd,
            "psswd": psswd,
            "speed": speed
        }

        print("[FPS_DEBUG] DRONE SPEED:", speed)
        print("[FPS_DEBUG] ENTERED PASSWORD:", psswd)

    # Остановка дрона
    elif cmd == 'stop':
        data = {
            "name": name,
            "command": cmd,
            "psswd": psswd
        }

        print(f'[FPS_STOP]')

    # Удаление дрона
    elif cmd == 'sign_out':
        drone.status = 'Initiated'
        drones.remove(drone)

        data = {
            "name": name,
            "command": cmd,
            "psswd": psswd
        }

        print(f'[FPS_SIGN_OUT]')

    # Новая задача для дрона
    elif cmd == 'new_task':
        data = {
            "name": name,
            "command": cmd,
            "points": content.get('points')
        }

        print(f'[FPS_NEW_TASK]')

    # Регистрация дрона
    elif cmd == 'register':
        data = {
            "name": name,
            "command": cmd,
            "psswd": psswd
        }

        print(f'[FPS_REGISTER]')

    # Отчистка дрона
    elif cmd == 'clear_flag':
        data = {
            "name": name,
            "command": cmd,
            "psswd": psswd
        }

        print(f'[FPS_CLEAR_FLAG]')

    if not data:
        return return_error(request)

    return send_request(drone, data)


@app.route("/data_in", methods=['POST'])
def data_in():
    try:
        content = request.json
    except Exception as e:
        return return_error(request)

    global drones

    try:
        drone = list(filter(lambda i: content['name'] == i.name, drones))
        if len(drone) > 1:
            print(f'[FPS_DATA_IN_ERROR]')
            print(f'Nonunique name: {content["name"]}')
            return "BAD ITEM NAME", 400

        drone = drone[0]
        print(f'[FPS_DATA_IN]')

        if content['operation'] == 'log':
            if content['msg'] == "Task finished":
                drone.status = 'Initiated'
                print(f'{content["name"]} successfully finished!')
            else:
                print(f'Successfully received {content}')
        elif content['operation'] == 'data':
            print(f'Successfully received {content}')
    except Exception as _:
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "new_task", "status": True})


@app.route("/atm_input", methods=['POST'])
def atm_input():
    content = request.json
    global drones
    try:
        drone = list(filter(lambda i: content['name'] == i.name, drones))
        if len(drone) > 1:
            print(f'[FPS_ATN_INPUT_ERROR]')
            print(f'Nonunique name: {content["name"]}')
            return "BAD ITEM NAME", 400

        if content['task_status'] == 'Accepted':
            data = {
               "name": content['name'],
               "points": content['points'],
               "command": 'set_task',
               "psswd": drone[0].psswd
            }
            requests.post(
                drone[0].endpoint,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
            print(f'[FPS_NEW_TASK]')
            print(f'Successfully accepted new task for {content["name"]}')
        else:
            print(f'[FPS_NEW_TASK_ERROR]')
            print(f'Something went wrong during accepting new task for {content["name"]}') 

    except Exception as _:
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "new_task", "status": True})


def main():
    """ Запуск системы планирования полётов. """
    global drones

    # Объявление дронов
    tmp = Drone(
        coordinate=(0,0,0),
        name="Generic1",
        psswd=12345,
        host="communication",
        port=6066
    )

    drones.append(tmp)
    print(f"Added drone {tmp.name} {tmp.endpoint}")

    app.run(port = port, host=host_name)
