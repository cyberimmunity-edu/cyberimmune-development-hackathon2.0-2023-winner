# Политики безопасности
policies = (
    # {"src": "communication", "dst": "authenticator", "opr": "initiate"},
    # {"src": "communication", "dst": "authenticator", "opr": "register"},
    # {"src": "authenticator", "dst": "data-analyze", "opr": "initiate"},
    # {"src": "authenticator", "dst": "data-analyze", "opr": "register"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "is_authorized"},
    # {"src": "authorization", "dst": "data-analyze", "opr": "send_is_authorized"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "authorize"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "verify_authorization"},
    # {"src": "authorization", "dst": "data-analyze", "opr": "set_access"},
    # {"src": "data-analyze", "dst": "manager", "opr": "send_error"},
    # {"src": "manager", "dst": "communication", "opr": "send_error"},
    # {"src": "data-analyze", "dst": "manager", "opr": "send_response"},
    # {"src": "manager", "dst": "communication", "opr": "send_response"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "atm_sign_up"},
    # {"src": "authorization", "dst": "send-atm", "opr": "atm_sign_up"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "atm_sign_out"},
    # {"src": "authorization", "dst": "send-atm", "opr": "atm_sign_out"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "atm_watchdog"},
    # {"src": "authorization", "dst": "send-atm", "opr": "atm_watchdog"},
    # {"src": "data-analyze", "dst": "authorization", "opr": "atm_data_in"},
    # {"src": "authorization", "dst": "send-atm", "opr": "atm_data_in"},
    # {"src": "ins", "dst": "nav", "opr": "set_ins_coords"},
    # {"src": "gnss", "dst": "nav", "opr": "set_gnss_coords"},

    {"src": "communication", "dst": "chipher", "opr": "initiate"},
    {"src": "communication", "dst": "chipher", "opr": "register"},
    {"src": "communication", "dst": "chipher", "opr": "set_token"},
    {"src": "communication", "dst": "chipher", "opr": "task_status_change"},
    {"src": "communication", "dst": "chipher", "opr": "start"},
    {"src": "communication", "dst": "chipher", "opr": "stop"},
    {"src": "communication", "dst": "chipher", "opr": "sign_out"},
    {"src": "communication", "dst": "chipher", "opr": "clear_flag"},
    {"src": "communication", "dst": "chipher", "opr": "set_task"},
    {"src": "chipher", "dst": "data-analyze", "opr": "process_command"},
    {"src": "data-analyze", "dst": "drone-data", "opr": "set_password"},
    {"src": "data-analyze", "dst": "drone-data", "opr": "set_token"},
    {"src": "data-analyze", "dst": "drone-data", "opr": "set_hash"},
    {"src": "data-analyze", "dst": "emergency", "opr": "stop"},
    {"src": "data-analyze", "dst": "manager", "opr": "process_command"},
    {"src": "drone-data", "dst": "communication", "opr": "send_response"},
    {"src": "drone-data", "dst": "communication", "opr": "send_error"},
    {"src": "manager", "dst": "drone-data", "opr": "send_response"},
    {"src": "manager", "dst": "drone-data", "opr": "send_error"},
    {"src": "manager", "dst": "autopilot", "opr": "move"},
    {"src": "autopilot", "dst": "servos", "opr": "move"},
    {"src": "autopilot", "dst": "manager", "opr": "set_move"},
    {"src": "manager", "dst": "processing", "opr": "get_data"},
    {"src": "processing", "dst": "def-storage", "opr": "get_data"},
    {"src": "def-storage", "dst": "storage", "opr": "get_data"},
    {"src": "storage", "dst": "def-storage", "opr": "send_data"},
    {"src": "def-storage", "dst": "manager", "opr": "send_data"},
    {"src": "data-analyze", "dst": "drone-data", "opr": "send_response"},
    {"src": "data-analyze", "dst": "drone-data", "opr": "send_error"},
    {"src": "drone-data", "dst": "chipher", "opr": "send_response"},
    {"src": "drone-data", "dst": "chipher", "opr": "send_error"},
    {"src": "chipher", "dst": "communication", "opr": "send_response"},
    {"src": "chipher", "dst": "communication", "opr": "send_error"},

    {"src": "data-analyze", "dst": "drone-data", "opr": "register"},
    {"src": "drone-data", "dst": "chipher", "opr": "register"},

    {"src": "manager", "dst": "drone-data", "opr": "sign_out"},

    {"src": "ins", "dst": "nav", "opr": "set_ins_coords"},
    {"src": "gnss", "dst": "nav", "opr": "set_gnss_coords"},
    {"src": "nav", "dst": "data-gruber", "opr": "set_coords"},
    {"src": "data-gruber", "dst": "health-check", "opr": "check"},
    {"src": "health-check", "dst": "battery", "opr": "get_battery"},
    {"src": "battery", "dst": "health-check", "opr": "set_battery"},
    {"src": "health-check", "dst": "data-gruber", "opr": "set_battery"},
    {"src": "battery-critical", "dst": "data-gruber", "opr": "low_power"},
    {"src": "data-gruber", "dst": "emergency", "opr": "stop"},
    {"src": "emergency", "dst": "emergency-servos", "opr": "land"},
    {"src": "data-gruber", "dst": "manager", "opr": "set_data"},
    {"src": "autopilot", "dst": "servos", "opr": "move"}
)

def check_operation(id, details) -> bool:
    """ Проверка возможности совершения обращения. """
    src: str = details.get("source")
    dst: str = details.get("deliver_to")
    opr: str = details.get("operation")

    if not all((src, dst, opr)):
        return False

    print(f"[info] checking policies for event {id},  {src}->{dst}: {opr}")

    return {"src": src, "dst": dst, "opr": opr} in policies
