import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dataset_processing import *

client_credentials_manager = SpotifyClientCredentials(
    client_id="d31b8fce2ead4943b1408cf3ba6f98bb",
    client_secret="08d00abdbb2b4f39891db99880dc819a")
sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)

genre_file = "msd-topMAGD-genreAssignment.txt"



for line in open('genre_file.txt'):



# Pop/Rock	238786
# Electronic	41075
# Rap	20939
# Jazz	17836
# R&B 14335

genres = {"Pop_Rock": 0, "Electronic": 0, "Rap": 0, "Jazz": 0, "RnB": 0}

for track in data:
    t_id = track[1]
    print track
    break;


# x = sp.search(q=test, limit=1)
#
# print x
