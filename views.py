# views.py
from flask import abort, jsonify, render_template, request, redirect, url_for, make_response, send_from_directory
import uuid

from app import app
import os
import glob
import json
import requests
import util
import util_spectrumannotation
import credentials
import urllib.parse

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{}"

@app.route('/', methods=['GET'])
def classicnetworking():
    response = make_response(render_template('homepage.html'))

    return response

@app.route('/analyzeupload', methods=['POST'])
def upload_1():
    upload_string = util.upload_single_file(request, "G1")
    response = make_response()
    response.set_cookie('selectedFiles', "True")

    return response
