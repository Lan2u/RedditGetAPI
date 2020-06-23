import requests
import webbrowser
import json
from flask import Flask, request, redirect

app = Flask(__name__)

# Used as part of the reddit api when getting an access token.
REDDIT_REDIRECT = 'http://localhost:8080/'

# Open the browser to this link so that the user can allow the app read permission.
REDDIT_REQ_PERMISSIONS = 'https://www.reddit.com/api/v1/authorize?client_id={clientId}&response_type=code&state={state}&redirect_uri={redirectUri}&duration=temporary&scope=read'

# Used to take the reddit api request code and convert it to an access token.
REDDIT_ACCESS_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'

# The url used to get the top posts for a subreddit (in json).
REDDIT_TOP_URL = 'https://oauth.reddit.com/r/{subreddit}/top/.json'

# The user agent used for connecting to the reddit API.
USER_AGENT = "windows:redditgetaviation:0.0.1 (by /u/Lan2u)"

CONFIG_PATH = "config.json"

# The config for connecting to the reddit api.
# Includes the clientId and secret aswell as the 'state' which is a unique string used for this API token request.
config = None

# The reddit access token / information, populated dynamically during setup.
reddit_access_token = None

def store_config(filename, config):
    cfg_file = open(filename, "w")
    cfg_file.write(json.dumps(config))
    cfg_file.close()

def load_config(filename):
    cfg = open(filename, "r")
    json_config = json.loads(cfg.read())
    cfg.close()
    return json_config

def register_reddit():
    webbrowser.open(REDDIT_REQ_PERMISSIONS.format(clientId=config['clientId'], redirectUri=REDDIT_REDIRECT, state=config['state']), 2)

def subreddit_top(subreddit):
    params = {
        't': 'day',
        'show': 'all',
        'limit': 10
    }

    header = {
        'User-agent': USER_AGENT,
        'Authorization': 'bearer' + reddit_access_token['access_token']
    }

    res = requests.get(url = REDDIT_TOP_URL.format(subreddit=subreddit), params=params, headers=header)

    res_json = res.json()

    result_file = open("response.json", "w")
    json.dump(res_json, result_file, sort_keys=True, indent=4)
    result_file.close()

    return res.text

@app.route('/ready', methods=['GET'])
def ready_page():
    res = subreddit_top('aviation')

    # Currently just sends the api respose 
    return res, 400

@app.route('/', methods=['GET'])
def register_response():
    state = request.args.get('state')
    code = request.args.get('code')
    if state != config['state']:
        return "Reddit response state doesn't match request", 403

    params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDDIT_REDIRECT
    }

    header = {'User-agent': USER_AGENT}

    res = requests.post(url = REDDIT_ACCESS_TOKEN_URL, params=params, auth=(config['clientId'], config['clientSecret']), headers = header)

    global reddit_access_token
    reddit_access_token = res.json()
    return redirect("http://localhost:8080/ready", code=301)

def prestart():
    print("Starting")
    global config
    config = load_config(CONFIG_PATH)
    register_reddit()


if __name__ == "__main__":
    prestart()
    app.run(debug=True, port=8080)