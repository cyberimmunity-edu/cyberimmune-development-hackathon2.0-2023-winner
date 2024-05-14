import requests

print('Simple test')
print('')
response = requests.post("http://127.0.0.1:6066/set_command", json={"name":"Generic1","psswd":"12345","coordinate":[0,0,0],"command": "initiate"})
print(response.json(), '-', response.status_code, end=' ')
if response.status_code == 200:
    print('OK! Test pass')
else:
    print('ERROR!')