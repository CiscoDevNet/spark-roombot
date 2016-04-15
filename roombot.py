from flask import Flask, request
import requests
import json
import configparser
from validate_email import validate_email
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter
import time
from threading import Timer
from flask.ext.cors import CORS
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
    with open( os.path.join(curDir, 'user_blacklist.txt'), 'r' ) as inFile:
        for line in inFile:
            if (userId in line) and (line[0] != '#'):
                blacklisted = True
    return blacklisted

def roomWhitelisted(roomId):
    whitelisted = False
    with open( os.path.join(curDir,'room_whitelist.txt'), 'r' ) as inFile:
        for line in inFile:
            if (roomId in line) and (line[0] != '#'):
                whitelisted = True
    return whitelisted

def refreshTokens():
    global accessToken
    accessToken = ''
    config = configparser.ConfigParser()
    config.read( os.path.join(curDir,'secrets.ini') )
    refreshToken = config.get('User', 'refreshToken')
    clientId = config.get('Spark App Secrets', 'clientId')
    clientSecret = config.get('Spark App Secrets', 'clientSecret')

    payload = { 'grant_type': 'refresh_token',
                'client_id': clientId,
                'client_secret': clientSecret,
                'refresh_token': refreshToken }

    header = {'Content-Type': 'application/json'}

    resp = requests.post('https://api.ciscospark.com/v1/access_token', headers=header, data=json.dumps(payload) )
    if resp.status_code != 200:
        log.error('Refresh token exchange failed')
        return

    respJson = resp.json()
    accessToken = respJson['access_token']
    tokenExpires = respJson['expires_in']
    log.info('Refresh token exchange successful')

    Timer(tokenExpires-(60*60), refreshTokens).start()

curDir = os.path.dirname(__file__)
log = logging.getLogger('rotating log')
log.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(curDir, 'roombot.log'), maxBytes=1048576, backupCount = 10)
handler.setFormatter(Formatter('%(asctime)s:%(levelname)s:%(message)s') )
log.addHandler(handler)

refreshTokens()

if __name__ == '__main__':
    application.run(host='0.0.0.0',debug=True)
