from flask import Flask, request
import requests
import json
import configparser
from validate_email import validate_email
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter
from flask_cors import CORS
import os

application = Flask(__name__)
CORS(application)

@application.route('/isUser', methods=['GET'])
def isUser():
    userId = request.args['user']

    header = {'Authorization': 'Bearer '+accessToken }

    resp = requests.get('https://api.ciscospark.com/v1/people?email='+userId, headers=header )

    respCode = resp.status_code

    if respCode == 200:
        respString = 'Success'
        found =  len( resp.json()['items'] ) > 0
        log.info('isUser: user='+userId+' Success')
    elif respCode == 400:
        respString = 'Invalid email'
        log.warn('isUser: user='+userId+' Invalid email')
    elif respCode == 401:
        respString = 'Unauthorized'
        log.error('isUser: GET failed unauthorized')
    else:
        respString = 'Unexpected response'
        log.warn('isUser returned Unexpected response')

    payload = json.dumps( {'status': respString, 'return': found} )

    return (payload,respCode,)

@application.route('/addUser', methods=['POST'])
def addUser():
    roomId = request.args['room']
    userId = request.args['user']

    log.info('adduser: user='+userId+' room='+roomId)

    if not validate_email(userId):
        log.warn('Invalid email address')
        return ( '{ "status": "Invalid email address"}', 400,)

    if userBlacklisted(userId):
        log.warn('User is blacklisted')
        return ( '{ "status": "User is blacklisted"}', 403,)

    if not roomWhitelisted(roomId):
        log.warn('Room is not whitelisted')
        return ( '{"status": "Room is not whitelisted"}', 403,)

    header = { 'Content-Type': 'application/json', 'Authorization': 'Bearer '+accessToken }
    body = { 'roomId': roomId, 'personEmail': userId }

    resp = requests.post('https://api.ciscospark.com/v1/memberships', headers=header, data=json.dumps(body) )

    respCode = resp.status_code

    if respCode == 200:
        respString = 'Success'
        log.info('POST /memberships succeeded')
    elif respCode == 400:
        respString = 'Invalid request'
        log.warn('POST /memberships returned Invalid request')
    elif respCode == 401:
        respString = 'Unauthorized'
        log.error('POST /memberships returned Unauthorized')
    elif respCode == 404:
        respString = 'Room does not exist'
        log.warn('POST /memberships returned Room does not exist')
    elif respCode == 409:
        respString = 'User already member of requested room'
        log.warn('POST /memberships returned User already member of requested room')
    else:
        respString = 'Unexpected response'
        log.warn('POST /memberships returned Unexpected response')

    payload = json.dumps( {'status': respString} )
    return (payload, respCode, )

def userBlacklisted(userId):
    blacklisted = False
    with open( os.path.join(curDir,'/config/','user_blacklist.txt'), 'r' ) as inFile:
        for line in inFile:
            if (userId == line.strip()):
                blacklisted = True
    return blacklisted

def roomWhitelisted(roomId):
    whitelisted = False
    with open( os.path.join(curDir,'/config/','room_whitelist.txt'), 'r' ) as inFile:
        for line in inFile:
            if (roomId == line.strip()):
                whitelisted = True
    return whitelisted

def readToken():
    global accessToken
    accessToken = ''
    config = configparser.ConfigParser()
    config.read( os.path.join(curDir,'/config/','secrets.ini') )
    accessToken = config.get('User', 'accessToken')

# File logging handler
curDir = os.path.dirname(__file__)
log = logging.getLogger('rotating log')
log.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(curDir, 'roombot.log'), maxBytes=1048576, backupCount = 10)
handler.setFormatter(Formatter('%(asctime)s:%(levelname)s:%(message)s') )

# Stdout (Kubernetes) handler
stdlog = logging.StreamHandler(sys.stdout)
stdlog.setLevel(logging.INFO)
stdlogformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdlog.setFormatter(stdlogformatter)

# Start logging
log.addHandler(handler)
log.addHandler(stdlogformatter)


readToken()

if __name__ == '__main__':
    application.run(host='0.0.0.0',port=5000,debug=True)
