from flask import Flask, render_template, redirect, request, jsonify
from flask import session
from requests import Request, post
import requests
import os

REDIRECT_URI = 'http://kabiltan.pythonanywhere.com/callback/'
CLIENT_ID = os.environ.get('ENV_CLIENT_ID')
CLIENT_SECRET = os.environ.get('ENV_CLIENT_SECRET')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('ENV_SECRET_KEY')

@app.route('/')
def index():
    return render_template('frontend.html')

@app.route('/', methods=['POST'])
def input():
    user_input = request.form['text']
    session['USER_INPUT'] = user_input
    number_of_songs = request.form['songs']
    session['SONG_NUMBER'] = number_of_songs
    playlist_name = request.form['playlist_name']
    session['PLAYLIST_NAME'] = playlist_name
    return redirect('http://kabiltan.pythonanywhere.com/redirect/', code=302)

@app.route('/redirect/')
def userLogin():
    scopes = 'user-read-recently-played user-top-read user-modify-playback-state playlist-modify-public playlist-modify-private'

    url = Request('GET', 'https://accounts.spotify.com/authorize', params={
        'scope': scopes,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID
    }).prepare().url
   
    return redirect(url, code=302)

@app.route('/callback/')
def callback():

    authorization_code = request.args.get('code')

    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }).json()

    access_token = response["access_token"]
    session['passing_access_token'] = access_token

    recently_played = requests.get('https://api.spotify.com/v1/me/player/recently-played', params={   
        'limit': 1,
    }, headers= {
        "Authorization": "Bearer {}".format(access_token),
    }).json()


    return redirect('http://kabiltan.pythonanywhere.com/success/', code=302)
    

@app.route('/success/')
def createPlaylist():
    access_token = session.get('passing_access_token', None)
    user_input = session.get('USER_INPUT', None)
    number_of_songs = session.get('SONG_NUMBER', None)
    playlist_name = session.get('PLAYLIST_NAME', None)

    user_data = requests.get('https://api.spotify.com/v1/me', headers={
        'Authorization' : "Bearer {}".format(access_token),
    }).json()

    USER_ID = user_data["id"]
    create_playlist = requests.post('https://api.spotify.com/v1/users/{user_id}/playlists'.format(user_id = USER_ID), headers= {
        'Authorization' : "Bearer {}".format(access_token),
    }, json={
        'name' : str(playlist_name)
    }).json()

    PLAYLIST_ID = create_playlist['id']

    tracks = requests.get('https://api.spotify.com/v1/search', headers= {
        'Authorization' : "Bearer {}".format(access_token),
    }, params= {
        'q' : user_input,
        'type' : 'track',
        'limit' : str(number_of_songs),
    }).json()

    
    list_of_track_uris = []
    for item in tracks['tracks']['items']:
        uri = item['uri']
        list_of_track_uris.append(uri)


    add_songs = requests.post('https://api.spotify.com/v1/playlists/{playlist_id}/tracks'.format(playlist_id = PLAYLIST_ID), headers= {
        'Authorization' : "Bearer {}".format(access_token),
        'Content-Type' : 'application/json'
    }, json= {
        'uris' : list_of_track_uris
    })

    return render_template('redirect.html')
    

if __name__ == '__main__':
    app.run(debug=True)