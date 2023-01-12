from flask import Flask, render_template, redirect, url_for, request
import main
import schedule
import time
import datetime

app = Flask(__name__)
lastStatus = 0

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html', lastRunningDate=None)
@app.route('/add_message')
def add_message():
    import start
    return render_template('summary.html', report=None)


# @app.route("/", methods=['GET'])
# def index():
#
#     # return render_template('index.html', lastRunningDate=main.getLastRunningDate())
#         return render_template('index.html', lastRunningDate=None)
# @app.route('/add_message')
# def add_message():
#     import main
#     main.runZTool()
#     return render_template('summary.html', report=main.getReport())
