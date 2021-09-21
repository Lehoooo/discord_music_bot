# Written By Leho | leho.dev | github.com/lehoooo
import json
import math
import re

import discord
import lavalink
import spotipy
from discord.ext import commands
from spotipy import SpotifyClientCredentials

url_rx = re.compile(r'https?://(?:www\.)?.+')

try:
    configopen = open("config.json", "r")
    config = json.load(configopen)
    configopen.close()
except Exception as e:
    print("Error Loading Config " + str(e))
    exit()


sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=str(config['spotify_client_id']),
                                                           client_secret=str(config['spotify_client_secret'])))



class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(str(config['lavalink_ip']), int(config['lavalink_port']), str(config['lavalink_password']), 'eu',
                                  'default-node')  # Host, Port, Password, Region, Name

            # Un Comment This For lava.link (public node)
            # bot.lavalink.add_node('lava.link', 80, 'youshallnotpass', 'eu',
            #                       'default-node')  # Host, Port, Password, Region, Name

            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('You need to be in my voicechannel.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await guild.change_voice_state(channel=None)


    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.

        if "https://open.spotify.com/track/" in query:
            # embed = discord.Embed(title="Track Queued!")
            results = sp.track(track_id=str(query))
            # print(results)
            # await ctx.send(str(results['name']) + " - " + str(results['artists'][0]['name']))

            results = await player.node.get_tracks("ytsearch:" + str(results['name']) + " " + str(results['artists'][0]['name']))
            # print(str(results))
            # embed.add_field(name="Song", value=str(results['artists'][0]['name']))


            track = results['tracks'][0]

            # await ctx.send(embed=embed)
            embed = discord.Embed(color=discord.Color.blurple())

            track = results['tracks'][0]

            embed.title = 'Track Queued!'
            embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")
            embed.description = "Title: ```" + track["info"]["title"] + "```\nLink: ```" + track["info"]["uri"] + "```"
            embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")
            await ctx.send(embed=embed)

            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
            if not player.is_playing:
                await player.play()


        elif "https://open.spotify.com/album/" in query:
            results = sp.album_tracks(album_id=str(query))
            embed = discord.Embed()
            totalsongs = 0
            for idx, track in enumerate(results['items']):
                totalsongs += 1
                print(track['name'] + " - " + track['artists'][0]['name'])
                results = await player.node.get_tracks("ytsearch:" + str(track['name']) + " " + str(track['artists'][0]['name']))
                track = results['tracks'][0]
                track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)
                if not player.is_playing:
                    await player.play()
            embed.title = 'Album Queued!'
            embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")
            embed.description = "Queued: ```" + str(totalsongs) + " Songs```"
            embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")
            await ctx.send(embed=embed)



        elif "https://open.spotify.com/playlist/" in query:
            results = sp.playlist(playlist_id=str(query))
            # print(results['tracks'])
            embed = discord.Embed()
            totalsongs = 0
            for idx, track in enumerate(results['tracks']['items']):
                totalsongs += 1
                # print(str(track['name']))
                # print(str(track['track']['name']) + " - " + str(track['track']['artists'][0]['name']))
                # embed.add_field(name=str(track['track']['name']), value=str(track['track']['artists'][0]['name']))
                results = await player.node.get_tracks("ytsearch:" + str(track['track']['name']) + " " + str(track['track']['artists'][0]['name']))
                track = results['tracks'][0]
                track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)
                if not player.is_playing:
                    await player.play()

            embed.title = 'Playlist Queued!'
            embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")
            embed.description = "Queued: ```" + str(totalsongs) + " Songs```"
            embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")
            await ctx.send(embed=embed)






        else:
            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            # Get the results for the query from Lavalink.
            results = await player.node.get_tracks(query)

            # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
            # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
            if not results or not results['tracks']:
                return await ctx.send('Nothing found!')

            embed = discord.Embed(color=discord.Color.blurple())

            # Valid loadTypes are:
            #   TRACK_LOADED    - single video/direct URL)
            #   PLAYLIST_LOADED - direct URL to playlist)
            #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
            #   NO_MATCHES      - query yielded no results
            #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
            if results['loadType'] == 'PLAYLIST_LOADED':
                tracks = results['tracks']

                for track in tracks:
                    # Add all of the tracks from the playlist to the queue.
                    player.add(requester=ctx.author.id, track=track)

                embed.title = 'Playlist Enqueued!'
                embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            else:
                track = results['tracks'][0]
                # embed.title = 'Track Queued!'
                # embed.description = track["info"]["title"] + " (" + track["info"]["uri"] + ")"

                embed.title = 'Track Queued!'
                embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")
                embed.description = "Title: ```" + track["info"]["title"] + "```\nLink: ```" + track["info"][
                    "uri"] + "```"
                embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")

                # You can attach additional information to audiotracks through kwargs, however this involves
                # constructing the AudioTrack class yourself.
                track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)

            await ctx.send(embed=embed)

            # We don't want to call .play() if the player is playing as that will effectively skip
            # the current track.
            if not player.is_playing:
                await player.play()

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page: int = 1):


        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if len(player.queue) == 0:
            await ctx.send(f"Now Playing: " + str(player.current.title))

        else:

            print(str(player.queue))

            items_per_page = 10
            pages = math.ceil(len(player.queue)) / items_per_page

            start = (page - 1) * items_per_page
            end = start + items_per_page
            embed = discord.Embed()
            embed.title = "Queue"
            embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")


            queue_list = ''
            queue_list += f"`{1}.` [**{player.current.title}**]({player.current.uri})\n"
            for index, track in enumerate(player.queue[start:end], start=start):
                index +=1
                queue_list += f"`{index + 1}.` [**{track.title}**]({track.uri})\n"
                embed.add_field(name=f"**{len(player.queue) + 1} tracks**", value=f"{queue_list}")
                # embed = discord.Embed(description=f"**{len(player.queue) + 1} tracks**\n{queue_list}")
                # embed.add_field(name="a", value="Currently Playing: " + str(player.current.title))
                embed.set_footer(text=f"Viewing page {page}/{pages}")
            embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")

            await ctx.send(embed=embed)

            # embed.description = "Queued: ```" + str(totalsongs) + " Songs```"


    @commands.command(aliases=['np'])
    async def playing(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # await ctx.send(f"Now Playing: " + str(player.current.title))

        a = round((player.position / 60000), 2)
        b = round((player.current.duration / 60000), 2)
        # await ctx.send(f"{a} / {b}")
        embed = discord.Embed()
        embed.title = 'Now Playing'
        embed.set_author(icon_url="https://cdn.discordapp.com/emojis/713547225883738143.gif", name="VibeBot")
        embed.description = "Song: ```" + str(player.current.title) + "```\nDuration: ```" + str(a) + " / " + str(b) + "```"
        embed.set_footer(text="""VibeBot | Made With 💖 By Leho""")
        await ctx.send(embed=embed)

    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        try:
            await player.skip()
            await ctx.send("Skipped!")
        except Exception as e:
            await ctx.send("Skip Failed! Error: " + str(e))

    @commands.command()
    async def clear(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        try:
            player.queue.clear()
            await ctx.send("Queue Cleared!")
        except Exception as e:
            await ctx.send("Failed To Clear Queue! Error: " + str(e))


    @commands.command()
    async def pause(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        try:
            await player.set_pause(True)
            await ctx.send("Paused!")
        except Exception as e:
            await ctx.send("Pause Failed! Error: " + str(e))

    @commands.command()
    async def resume(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        try:
            await player.set_pause(False)
            await ctx.send("Resumed!")
        except Exception as e:
            await ctx.send("Resume Failed! Error: " + str(e))


    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send('You\'re not in my voicechannel!')

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.guild.change_voice_state(channel=None)
        await ctx.send('Disconnected!')



def setup(bot):
    bot.add_cog(Music(bot))
