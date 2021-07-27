import json

with open('managers.json') as file:
    managers = json.load(file)

print(managers['managers'])