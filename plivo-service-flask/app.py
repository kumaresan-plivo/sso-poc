from flask import Flask, request, make_response, Response, url_for
import requests
import json
import time

app = Flask(__name__)

STORMPATH_REAUTH_URL = 'https://api.stormpath.com/v1/applications/pEp9AjaSOFUBV0iMGKgIs/authTokens/%s'
STORMPATH_API_KEY = '38TL5ZCCAO5T04PDDS8UR5CEL'
STORMPATH_API_SECRET = 'FDzts7tX2PEQw4v0JhLZVlkHAnXzAlcsXkEoZ/Mx9JU'

sso_r = requests.Session()
sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)


@app.route('/complex_op', methods=['POST'])
def complex_op():
    access_token = request.headers['Authorization'][7:]

    # post to SSO to check token validity
    sso_resp = sso_r.get(str.format(STORMPATH_REAUTH_URL % access_token))
    print(sso_resp.text)

    if sso_resp.ok:
        access_token = sso_resp.json()['jwt']
    else:
        # TODO refresh AT from cached RT
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

