from flask import Flask, request, Response, make_response, url_for, render_template, redirect, flash
import jwt
import redis
import requests

app = Flask(__name__)
app.secret_key = 'QAL4rhJtQDSYQMFNldEF'

STORMPATH_APP_BASE_URL = 'https://api.stormpath.com/v1/applications/pEp9AjaSOFUBV0iMGKgIs'
STORMPATH_AUTH_URL = STORMPATH_APP_BASE_URL + '/oauth/token'
STORMPATH_API_KEY = '38TL5ZCCAO5T04PDDS8UR5CEL'
STORMPATH_API_SECRET = 'FDzts7tX2PEQw4v0JhLZVlkHAnXzAlcsXkEoZ/Mx9JU'

sso_r = requests.Session()
sso_r.auth = (STORMPATH_API_KEY, STORMPATH_API_SECRET)
cache = redis.Redis()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.values.get('username')
    password = request.values.get('password')

    # post to SSO with password grant
    params = {'username': username,
              'password': password,
              'grant_type': 'password'}

    response = sso_r.post(STORMPATH_AUTH_URL, params)
    print(response.text)

    if response.ok:
        at = response.json()['access_token']
        rt = response.json()['refresh_token']
        # cache AT, RT
        # decoded_token = jwt.decode(at, STORMPATH_API_SECRET, algorithms=['HS256'])
        token_cache = {'refresh_token': rt,
                       'username': username}
        cache.hmset(at, token_cache)
        cache.expire(at, response.json()['expires_in'])
        # redirect to dashboard
        flash("You've successfully logged in!")
        response = make_response(render_template('dashboard.html', username=username))
        response.set_cookie('token', at, secure=False)  # TODO need SSL for secure flag
        return response
    else:
        flash(response.json()['message'])
        return redirect(url_for('index'))


@app.route('/resource', methods=['POST', 'GET'])
def resource():
    # quickly validate cached AT and return resource
    access_token = request.cookies.get('token')
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
            return Response('YASSS')
        else:
            print("We've dun goofed!", issuer, STORMPATH_APP_BASE_URL)
            return Response('NAHIIIIIIIIIII')
    else:
        print("We've dun goofed!", username_rt, username_at)
        return Response('NAHIIIIIIIIIII')


@app.route('/complex_op', methods=['POST', 'GET'])
def complex_op():
    access_token = request.cookies.get('token')

    token_header = str.format('Bearer %s' % access_token)
    response = requests.post('http://localhost:3000/complex_op', headers={'Authorization': token_header})
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
