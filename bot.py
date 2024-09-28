import discord
from discord import app_commands
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from google.generativeai import *

load_dotenv()
api_token = os.getenv('MY_API_TOKEN')
if api_token is None:
    raise ValueError("API token is not set in environment variables")
api_key = os.getenv('MY_API_KEY')
configure(api_key=api_key)

intents = discord.Intents.default()
intents.message_content = True
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
         
async def summarize(channel_id, prompt):
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
            title="要約結果",
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
        await summarize(channel_id,"次の文章を6000字以内で要約してください：")
        await interaction.followup.send("処理が終了しました")
    except Exception as e:
        print(e)

@client.tree.command(name="mvp", description="24時間のMVP")
async def mvp(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        await fetch_messages(channel_id)
        await summarize(channel_id,"次の文章からMVP(最も格好良い発言)を選んでください：")
        await interaction.followup.send("処理が終了しました")
    except Exception as e:
        print(e)



client.run(api_token)

