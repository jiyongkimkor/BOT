import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from youtube_dl import YoutubeDL
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        #all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

        self.a = []
        self.b = []

    def parsing(self, item):
        path = 'C:/Users/Jiyong/Desktop/coding/Pycharm/chromedriver'
        feature = item
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(path, options=options)
        driver.get('https://www.youtube.com')


        print('웹페이지를 불러오는 중입니다..')
        src = driver.find_element(By.NAME,"search_query")
        src.send_keys(feature)
        src.send_keys(Keys.RETURN)
        time.sleep(1)
        print('검색 결과를 불러오는 중입니다..')
        time.sleep(1)
        print('데이터 수집 중입니다....')
        lxml = driver.page_source
        soup = BeautifulSoup(lxml, features='lxml')
        time.sleep(1)

        df_title = []
        df_link = []


        for i in range(
                len(soup.find_all('ytd-video-meta-block', 'style-scope ytd-video-renderer byline-separated'))):
            title = soup.find_all('a', {'id': 'video-title'})[i].text.replace('\n', '')
            link = 'https://www.youtube.com/' + soup.find_all('a', {'id': 'video-title'})[i]['href']

            df_title.append(title)
            df_link.append(link)

        return df_title, df_link

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}


    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            print(self.music_queue)
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="find", help="search a selected song from youtube")
    async def f(self, ctx, *args):
        query = " ".join(args)
        self.a, self.b = self.parsing(query)
        print(self.a)
        embed = discord.Embed(
            title="Music List",
            description="result",
            colour=discord.Color.blue()
        )

        for i in range(0,len(self.a)):
            embed.add_field(name=str(i + 1) + 'GACHIMUCHI', value='\n' + '[%s](<%s>)' % (self.a[i], self.b[i]),
                                inline=False)

        await ctx.send(ctx.channel, embed=embed)

    @commands.command(name="play", help="Plays a selected song from youtube")
    async def p(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send("Connect to a voice channel!")
        else:
            for i in range(0, len(self.b)):
                if int(query[0])-1 == i:
                    song = self.search_yt(self.b[i])
                    if type(song) == type(True):
                        await ctx.send(
                            "Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
                    else:
                        await ctx.send("Song added to the queue")
                        self.music_queue.append([song, voice_channel])

                        if self.is_playing == False:
                            await self.play_music()

    @commands.command(name="queue", help="Displays the current songs in queue")
    async def q(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music()
            
    @commands.command(name="disconnect", help="Disconnecting bot from VC")
    async def dc(self, ctx):
        await self.vc.disconnect()
