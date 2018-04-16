#import statements
import requests
import json

#client tokens for spotify
client_id = '2efb491c8f8b49e6825224f3491a1e6e'
client_secret = '828d2c8abb9f407489ea390451d5d9fb'


#in this function, you will pass in a term/phrase of what type/kind of playlist you are looking for. it will then return a search object with a dictionary of playlist information
def get_spotify(term):
    oauth_token = "BQD9dTfBQLNX2Ci2HyLSRME9vCIlmtFuYPZFPVZhNkxrv1E0DOTPsEJNFu8gtOxBDfaLS9Xb51NZJ4RMpvmx7CP1ZN7NzFJQKQYLzI61FZc0B85Fzgv32YomBLxLlB2oA3i5Fs56VWDE7Le6A_QO-cMy1j98wFKWrjY" #oauth token for spotify
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
        print(item)
        playlist_name = item['name']
        playlist_id = item['id']
        user_id = item['owner']['id']
        cover_pic = item['images'][0]['url']
        print(cover_pic)
        list_of_names.append((playlist_name,playlist_id, user_id, cover_pic))
    return(list_of_names)
print(get_playlist_info('running'))

#this function will use a tupple (containing playlist name, id, and user_id) and make another request to spotify to get the tracks and artists for each playlist
def get_playlist_songs_and_artist(tupple):
    songs_and_artists = []
    oauth_token = "BQAVhLvaDkhPII_qNBURcrjL0B4T-038NOG5i96cttghdFZnrzlABEueS--puYg33Yx0op6ccX7YNTHjc3gGv26VAkD2H0XtOqv7blYzM3tQ3JxeHWcEd77XAbog_Aap5CMWQiWmnY15oNd65PlbFFc3WdKLYqpolTI" #you need to generate the OAuth token from https://beta.developer.spotify.com/console/get-search-item/
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


# have to serach for a term --> get_spotify

#after picking playlist from get spotify --> use get_playlist_info

#after getting playlist unfo, use that info for get_playlist_songs_and_artist



# print(get_playlist_songs_and_artist(('Old Drake Mix', '5wa2aJtbvejnwMORdP5tth', 'neeksldn')))
