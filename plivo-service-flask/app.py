from flask import Flask, request, make_response, Response, url_for
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

sso_r = requests.Session()
sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)
cache = redis.Redis()


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
        decoded_token = jwt.decode(access_token, STORMPATH_API_SECRET, algorithms=['HS256'])
        print(decoded_token)
        issuer = decoded_token['iss']
        if issuer == STORMPATH_APP_BASE_URL:
            print("Token valid..")
            return Response('YASSS')
        else:
            print("We've dun goofed!", issuer, STORMPATH_APP_BASE_URL)
            return Response('NAHIIIIIIIIIII')
    else:
        print("We've dun goofed!", username_rt, username_at)
        return Response('NAHIIIIIIIIIII')


@app.route('/complex_op', methods=['POST'])
def complex_op():
    access_token = request.headers['Authorization'][7:]
    use_rt_flow = request.form['use_rt_flow']
    username = request.form['username']
    if use_rt_flow:
        # refresh AT from cached RT
        rt = cache.hmget(access_token, 'refresh_token')[0]
        params = {'refresh_token': rt,
                  'grant_type': 'refresh_token'}

        response = sso_r.post(STORMPATH_REAUTH_URL, params)
        print(response.text)

        if response.ok:
            at = response.json()['access_token']
            rt = response.json()['refresh_token']
            # cache AT, RT
            token_cache = {'refresh_token': rt,
                           'username': username}
            cache.hmset(at, token_cache)
            cache.expire(at, response.json()['expires_in'])
    else:
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

