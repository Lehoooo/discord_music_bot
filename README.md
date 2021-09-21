# discord_music_bot
A simple Discord bot to play music into a voice channel with support for Spotify & Youtube. 

# Features
* Can play Spotify playlists, albums, and songs
* Can play any video from youtube
* Fast
* Uses lavalink - streams songs instead of downloading

# Installation
* ```pip3 install discord.py lavalink requests spotipy```
* Rename ```config_example.json``` to ```config.json```
* Fill ```config.json``` with your tokens & lavalink server info
* Run The Bot ```python3 main.py``` 

# Usage
```python3 main.py```

# How To Get Spotify Tokens
* Go To ```https://developer.spotify.com/dashboard/applications```
* Create a new app
* Copy the Client ID and Client Secret
* Put into ```config.json```
* Done 

# Note!
This bot does require you to run a lavalink server, although there are some public ones (https://support.something.host/en/article/lavalink-hosting-okm26z/), Using these are at your own risk. I will not provide support for public lavalink servers.
