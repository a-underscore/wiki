import json
import os

from flask import Flask

with open(os.path.join(os.getcwd(), "config.json")) as file:
    config = json.load(file)

    app = Flask(config["PROJECT_NAME"])
    app.config.update(config)
