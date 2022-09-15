from flask import Flask, render_template, redirect, url_for, request
from collections import namedtuple


app = Flask(__name__)

message = namedtuple('Message', 'text tag')
messages = []

@app.route("/", methods=['GET'])
def index():

    return render_template('index.html')

@app.route('/add_message')
def add_message():
    import myTestFile
    return f"SUMMARY {myTestFile.runZTool()}"


