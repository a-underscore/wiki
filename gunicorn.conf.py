import os
import json

with open(os.path.join(os.getcwd(), "config.json")) as file:
    conf = json.load(file)

wsgi_app = "run:run_app()"
bind = f'{conf.get("SERVER_ADDRESS")}:{conf.get("SERVER_PORT")}'
workers = 4
reload = True
