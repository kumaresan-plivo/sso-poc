from flask import Flask, request, make_response, url_for, render_template, redirect, flash, send_file, Response
import json
import redis
import requests

app = Flask(__name__)
app.secret_key = 'QAL4rhJtQDSYQMFNldEF'

STORMPATH_APP_BASE_URL = 'https://api.stormpath.com/v1/applications/pEp9AjaSOFUBV0iMGKgIs'
STORMPATH_AUTH_URL = STORMPATH_APP_BASE_URL + '/oauth/token'
STORMPATH_API_KEY = '38TL5ZCCAO5T04PDDS8UR5CEL'
STORMPATH_API_SECRET = 'FDzts7tX2PEQw4v0JhLZVlkHAnXzAlcsXkEoZ/Mx9JU'
STORMPATH_GROUP_URL = STORMPATH_APP_BASE_URL + '/accounts?username=%s&expand=groups'

LOCAL_SSO_AUTH_URL = 'http://localhost:8000/oauth/token/'
LOCAL_SSO_API_KEY = 'fXiZ1hAqsSXns47gCypqqIYfNP7cIU7vdKoVrk1S'
LOCAL_SSO_API_SECRET = '8OpksytwMpvqdXhu3SXvbAs5WRlyyw6JIbmgFeaqP9AcypYm1dtZXmW4UpAZAznIU41pp6F0q7nfqMvR1pAZbRgBZW06dw1jDT6aER2kYT33GLllPWetBaY4kYFWMpEM'

sso_r = requests.Session()
cache = redis.Redis()
use_local_sso = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.values.get('username')
    password = request.values.get('password')
    global use_local_sso
    use_local_sso = request.values.get('use_local_sso')

    # post to SSO with password grant
    params = {'username': username,
              'password': password,
              'grant_type': 'password'}

    sso_url = LOCAL_SSO_AUTH_URL if use_local_sso else STORMPATH_AUTH_URL
    if use_local_sso:
        sso_r.auth = (LOCAL_SSO_API_KEY, LOCAL_SSO_API_SECRET)
    else:
        sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)
    response = sso_r.post(sso_url, params)
    print(response.text)

    if response.ok:
        at = response.json()['access_token']
        rt = response.json()['refresh_token']
        expiry = response.json()['expires_in']
        try:
            scopes = response.json()['scope']
        except KeyError:
            scopes = None
            if not use_local_sso:
                # get scopes from stormpath
                # 1. get expanded groups for the user
                response = sso_r.get(str.format(STORMPATH_GROUP_URL % username))
                print(response.text, response.url)
                # 2. get the customData from groups
                response = sso_r.get(response.json()['items'][0]['groups']['items'][0]['customData']['href'])
                print(response.text)
                scopes = response.json()['scopes']

        # cache AT, RT
        token_cache = {'refresh_token': rt,
                       'username': username,
                       'scopes': scopes}
        cache.hmset(at, token_cache)
        cache.expire(at, expiry)
        # redirect to dashboard
        flash("You've successfully logged in!")
        response = make_response(render_template('dashboard.html', username=username))
        response.set_cookie('token', at, secure=False)  # TODO need SSL for secure flag
        return response
    else:
        flash(response.json()['error_description'] if use_local_sso else response.json()['message'])
        return redirect(url_for('index'))


@app.route('/resource', methods=['POST', 'GET'])
def resource():
    access_token = request.cookies.get('token')
    res_url = 'http://localhost:3000/resource?username=%s'
    response = requests.get(str.format(res_url % request.values.get('username')), headers={'Authorization': access_token})
    if response.text == 'YES':
        return send_file('./fry_yes.jpg', mimetype='image/jpeg')
    else:
        return send_file('./fry_no.jpg', mimetype='image/jpeg')


@app.route('/complex_op', methods=['POST', 'GET'])
def complex_op():
    access_token = request.cookies.get('token')

    token_header = str.format('Bearer %s' % access_token)
    global use_local_sso
    response = requests.post('http://localhost:3000/complex_op',
                             data={'use_rt_flow': True if request.form.get('use_rt_flow') else None,
                                   'username': request.form['username'],
                                   'use_local_sso': use_local_sso},
                             headers={'Authorization': token_header})
    print(response.text)

    # reset the token if we obtain a new one in case of AT expiry
    try:
        token = response.headers['Authorization']
        token = token[7:]  # cut off the Bearer part
    except KeyError:
        token = access_token
    response = make_response(response.text)
    response.set_cookie('token', token)
    return response


@app.route('/logout')
def logout():
    # remove redis cache
    access_token = request.cookies.get('token')
    cache.delete(access_token)

    # clear cookies
    response = make_response(redirect(url_for('index')))
    response.set_cookie('token', '', expires=0)
    return response


if __name__ == '__main__':
    app.run(debug=True)
