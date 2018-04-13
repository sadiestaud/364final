#import statements
import requests
import json

#client tokens for spotify
client_id = '2efb491c8f8b49e6825224f3491a1e6e'
client_secret = '828d2c8abb9f407489ea390451d5d9fb'


#in this function, you will pass in a term/phrase of what type/kind of playlist you are looking for. it will then return a search object with a dictionary of playlist information
def get_spotify(term):
    oauth_token = "BQBzjyW0jy8e9rE5-WwzHmfOdjlkfYH8S32vivLnPks-eY4OQ3ofh-K0NQz2Z5hcFrXNhZW2Xs2bgeHdggjvfBA76W8Kad1-OS1nUdZz5VKNQl1J5AWWLmej8tLjwrB3vYiLmXmq4sLOZVcQfHBRY-fBwnysONacqtU" #oauth token for spotify
    headers ={"Content-Type": "application/json", "Authorization": "Bearer " + oauth_token}
    params = { 'q': term, 'type': 'playlist'} #q is any term that will be used to get a playlsit
    search_object = requests.get('https://api.spotify.com/v1/search?', headers=headers, params = params).json() #search object
    playlists = search_object['playlists']['items'] #get the playlist items
    return(playlists)
# print(get_spotify('running'))

#this function will take in a term and then use the get_spotify function to recieve list of tupples for each playlist. each tupple will contain a playlist's name, id, and user_id
def get_playlist_info(term):
    list_of_playlist_dicts = get_spotify(term)
    list_of_names = []
    for item in list_of_playlist_dicts:
        playlist_name = item['name']
        playlist_id = item['id']
        user_id = item['owner']['id']
        list_of_names.append((playlist_name,playlist_id, user_id))
    return(list_of_names)
# print(get_playlist_titles('running'))

#this function will use a tupple (containing playlist name, id, and user_id) and make another request to spotify to get the tracks and artists for each playlist
def get_playlist_songs_and_artist(tupple):
    songs_and_artists = []
    oauth_token = "BQDg-GhULd4J0ukmAC0w59US6tyJ5apiZjILbo0aKwVjUJVA-ax_2cegJITOeC_Dpvsg4IHPOXvhe1qIFAzg5OSqyaD2Xq-66Dn0w61d4EtFZRSIRaAo7Y_Zt-N0YY5p9m95esqHzvbi0uBesw7Uv1ZWLOlcNXGHHVw" #you need to generate the OAuth token from https://beta.developer.spotify.com/console/get-search-item/
    headers ={"Content-Type": "application/json", "Authorization": "Bearer " + oauth_token}
    search_object = requests.get('https://api.spotify.com/v1/users/'+tupple[2]+'/playlists/'+tupple[1]+'/tracks', headers=headers).json()['items']#[0]['track']
    for item in search_object:
        song = item['track']['name']
        all_artists = item['track']['artists']
        artist_list = []
        for a in all_artists:
            artist = a['name']
            artist_list.append(artist)
        tup = (song,artist_list)
        songs_and_artists.append(tup)
    return(songs_and_artists)
# print(get_playlist_songs_and_artist(('Old Drake Mix', '5wa2aJtbvejnwMORdP5tth', 'neeksldn')))
