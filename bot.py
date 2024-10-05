import discord
from discord import app_commands
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from google.generativeai import *
from gtts import gTTS
import asyncio
from discord.ext import commands

load_dotenv()
api_token = os.getenv('MY_API_TOKEN')
if api_token is None:
    raise ValueError("API token is not set in environment variables")
api_key = os.getenv('MY_API_KEY')
configure(api_key=api_key)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

# サーバーごとにボイスチャンネルとテキストチャンネルを記録する辞書
selected_text_channel = {}
selected_voice_channel = {}

g_str = ""
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

async def fetch_messages(channel_id):
    channel = client.get_channel(channel_id)
    if channel is None:
        print("ch not found")
        return

    one_day_ago = datetime.utcnow() - timedelta(days=1)

    messages = []
    async for message in channel.history(after=one_day_ago):
        if not message.author.bot:
            messages.append(message)
    str = ""
    if not messages:
        print("message not found")
        return
    for message in messages:
        #print(f"{message.author}: {message.content}")
        str+=f"{message.author}: {message.content}\n"

    global g_str
    g_str = str[:]
    #print(g_str)
         
async def summarize(channel_id, prompt, title):
    try:
        global g_str
        #print("g_str")
        #print(g_str)
        channel = client.get_channel(channel_id)
        if channel is None:
            print("channel is none")
            return
        str = prompt + g_str
        #print(str)
        model = GenerativeModel("gemini-pro")
        gt = model.generate_content(str)
        #print(gt.text)
        #print(gt.candidates)
        embed = discord.Embed(
            title=title,
            description=gt.text,
            color=0x00ff00
        )
        await channel.send(embed=embed)
    except Exception as e:
        print(e)

#await interaction.response.send_message(f"Current Channel id: {channel_id}")
@client.tree.command(name="要約", description="過去一日分のメッセージを要約します")
async def get_messages(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        await fetch_messages(channel_id)
        await summarize(channel_id,"次の文章を6000字以内で要約してください：","要約結果")
        await interaction.followup.send("処理が終了しました")
    except Exception as e:
        print(e)

@client.tree.command(name="mvp", description="24時間のMVP")
async def mvp(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        await fetch_messages(channel_id)
        await summarize(channel_id,"次の文章からMVP(最も格好良い発言)を選んでください：","MVP")
        await interaction.followup.send("処理が終了しました")
    except Exception as e:
        print(e)

@client.tree.command(name="vc参加", description="BOTをVCに参加させます")
async def join(interaction: discord.Interaction):
    try:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            selected_text_channel[interaction.guild.id] = interaction.channel.id
            selected_voice_channel[interaction.guild.id] = channel.id
            await interaction.response.send_message(f"{channel}に参加しました", ephemeral=True)
        else:
            await interaction.response.send_message("まずVCに参加してください", ephemeral=True)
    except Exception as e:
        print(e)

@client.tree.command(name="vc退出", description="BOTをVCから退出させます")
async def leave(interaction: discord.Interaction):
    try:
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            selected_text_channel.pop(interaction.guild.id, None)
            selected_voice_channel.pop(interaction.guild.id, None)
            await interaction.response.send_message("VCから退出しました", ephemeral=True)
        else:
            await interaction.response.send_message("VCに接続していません", ephemeral=True)
    except Exception as e:
        print(e)

# メッセージが投稿された時に呼ばれるイベント
@client.event
async def on_message(message):
    try:
        # Bot自身または他のBotのメッセージは無視
        if message.author.bot:
            return

        guild_id = message.guild.id

        # サーバーごとに設定されたテキストチャンネルかどうか確認
        if guild_id not in selected_text_channel or selected_text_channel[guild_id] != message.channel.id:
            return  # 設定されたチャンネル以外のメッセージは無視

        vc = message.guild.voice_client
        if not vc:
            return  # ボイスチャンネルに接続していない場合は処理しない

        # メッセージ内容を取得
        text = message.content.strip()
        
        # Google Text-to-Speechを使って音声ファイルを生成
        tts = gTTS(text=text, lang='ja')
        tts.save("message.mp3")
        
        # ボイスチャンネルでメッセージを再生
        vc.play(discord.FFmpegPCMAudio("message.mp3"), after=lambda e: print("done", e))
        
        # 再生終了を待機
        while vc.is_playing():
            await asyncio.sleep(1)

        # 一時ファイルを削除
        os.remove("message.mp3")

    except Exception as e:
        print(e)

client.run(api_token)

