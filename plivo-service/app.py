from flask import Flask, request, send_file, Response
from jwt.exceptions import DecodeError
import jwt
import json
import redis
import requests
import time

app = Flask(__name__)

STORMPATH_APP_BASE_URL = 'https://api.stormpath.com/v1/applications/pEp9AjaSOFUBV0iMGKgIs'
STORMPATH_AUTH_VERIFY_URL = STORMPATH_APP_BASE_URL + '/authTokens/%s'
STORMPATH_REAUTH_URL = STORMPATH_APP_BASE_URL + '/oauth/token'
STORMPATH_API_KEY = '38TL5ZCCAO5T04PDDS8UR5CEL'
STORMPATH_API_SECRET = 'FDzts7tX2PEQw4v0JhLZVlkHAnXzAlcsXkEoZ/Mx9JU'

LOCAL_SSO_AUTH_URL = 'http://localhost:8000/oauth/token'
LOCAL_SSO_API_KEY = 'fXiZ1hAqsSXns47gCypqqIYfNP7cIU7vdKoVrk1S'
LOCAL_SSO_API_SECRET = '8OpksytwMpvqdXhu3SXvbAs5WRlyyw6JIbmgFeaqP9AcypYm1dtZXmW4UpAZAznIU41pp6F0q7nfqMvR1pAZbRgBZW06dw1jDT6aER2kYT33GLllPWetBaY4kYFWMpEM'

sso_r = requests.Session()
sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)
cache = redis.Redis()
use_local_sso = False


@app.route('/resource', methods=['GET'])
def resource():
    # quickly validate cached AT and return resource
    access_token = request.headers['Authorization']
    # 1. check if AT hasn't expired and AT username equals cache username
    username_at = cache.hmget(access_token, 'username')[0]
    username_at = username_at.decode('utf-8')
    username_rt = request.values.get("username")
    if username_at == username_rt:
        # 2. decode token(checks signature) and check issuer
        try:
            decoded_token = jwt.decode(access_token, STORMPATH_API_SECRET, algorithms=['HS256'])
            print(decoded_token)
            issuer = decoded_token['iss']
            assert issuer == STORMPATH_APP_BASE_URL
        except DecodeError:
            print("Ignoring jwt decode error")

        print("Token valid..")
        return Response('YES')
    else:
        print("We've dun goofed!", username_rt, username_at)
        return Response('NAHIIIIIIIIIII')


@app.route('/complex_op', methods=['POST'])
def complex_op():
    print  (request.form)
    access_token = request.headers['Authorization'][7:]
    use_rt_flow = True if request.form.get('use_rt_flow') else False
    username = request.form['username']
    global use_local_sso
    use_local_sso = True if request.form.get('use_local_sso') else False

    # first check if AT has ComplexScope
    scopes = cache.hmget(access_token, 'scopes')[0]
    if 'ComplexScope' not in scopes.decode('utf-8'):
        params = {'result': 'FAIL', 'message': 'Access token does not have valid scopes'}
        print (scopes.decode('utf-8'))
        resp = Response(json.dumps(params), mimetype='text/json')
        return resp

    if use_rt_flow:
        # refresh AT from cached RT
        rt = cache.hmget(access_token, 'refresh_token')[0]
        params = {'refresh_token': rt,
                  'grant_type': 'refresh_token'}

        sso_url = LOCAL_SSO_AUTH_URL if use_local_sso else STORMPATH_REAUTH_URL
        if use_local_sso:
            sso_r.auth = (LOCAL_SSO_API_KEY, LOCAL_SSO_API_SECRET)
        else:
            sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)
        response = sso_r.post(sso_url, params)
        print(response.text)

        if response.ok:
            at = response.json()['access_token']
            rt = response.json()['refresh_token']
            # cache AT, RT
            token_cache = {'refresh_token': rt,
                           'username': username,
                           'scopes': scopes}  # Bad, should get recent AT scopes, but that involves more coding
            cache.hmset(at, token_cache)
            cache.expire(at, response.json()['expires_in'])
    elif not use_local_sso:
        # post to SSO to check token validity
        sso_resp = sso_r.get(str.format(STORMPATH_AUTH_VERIFY_URL % access_token))
        print(sso_resp.text)

        if sso_resp.ok:
            access_token = sso_resp.json()['jwt']
        else:
            params = {'result': 'FAIL', 'message': 'Token re-auth failed'}
            resp = Response(json.dumps(params), mimetype='text/json')
            return resp

    # do OPS???
    time.sleep(3)

    # send back a response with new/same AT
    params = {'result': 'OK', 'message': 'All iz well'}
    resp = Response(json.dumps(params), mimetype='text/json')
    resp.headers['Authorization'] = str.format('Bearer %s' % access_token)
    return resp


if __name__ == '__main__':
    app.run(port=3000, debug=True)

