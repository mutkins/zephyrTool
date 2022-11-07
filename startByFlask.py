from flask import Flask, render_template, redirect, url_for, request
from collections import namedtuple

import main

app = Flask(__name__)


@app.route("/", methods=['GET'])
def index():

    return render_template('index.html', lastRunningDate=main.getLastRunningDate())

@app.route('/add_message')
def add_message():
    main.runZTool()
    return render_template('summary.html', report=main.getReport())

