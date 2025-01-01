import discord
from discord import app_commands
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from google.generativeai import *
from gtts import gTTS
import asyncio
from discord.ext import commands
import re
print("Hello, Railway!",flush=True)
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

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient(intents=intents)

@client.event
async def on_voice_state_update(member, before, after):
    voice_channel = None
    for vc in client.voice_clients:
        if vc.guild == member.guild:
            voice_channel = vc.channel
            break

    # ボットがVCに参加しているかどうか確認
    if voice_channel and len(voice_channel.members) == 1 and voice_channel.members[0] == client.user:
        await client.voice_clients[0].disconnect()  # ボットを退出させる
        print("VCにボットだけが残っているため、退出しました。")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

def remove_urls(text):
    """
    URLを削除する関数
    http:// または https:// で始まる文字列を削除
    """
    return re.sub(r'http[s]?://\S+', '', text)
    
def remove_custom_emojis(text):
    """
    Discordのカスタム絵文字を削除する関数
    <:emoji_name:emoji_id> や <a:emoji_name:emoji_id>（アニメーション絵文字）を削除
    """
    return re.sub(r'<a?:\w+:\d+>', '', text)

def remove_unicode_emojis(text):
    """
    ユニコードの絵文字を削除する関数
    笑顔やシンボル、乗り物など、幅広い絵文字を削除
    """
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 笑顔の絵文字
        "\U0001F300-\U0001F5FF"  # シンボル & 絵文字
        "\U0001F680-\U0001F6FF"  # 乗り物 & 絵文字
        "\U0001F1E0-\U0001F1FF"  # 旗の絵文字
        "\U00002702-\U000027B0"  # その他の記号
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def remove_mentions(text):
    """
    メンションを削除する関数
    <@user_id> や @everyone, @here, @username を削除
    """
    # メンション形式 <@user_id>, <@!user_id>, <@&role_id> の削除
    text = re.sub(r'<@!?&?\d+>', '', text)
    # 通常のメンション @everyone, @here, @username の削除
    return re.sub(r'@\w+', '', text)

def clean_text(text):
    """
    URL、カスタム絵文字、ユニコード絵文字、メンションを削除する
    """
    text = remove_urls(text)
    text = remove_custom_emojis(text)
    #text = remove_unicode_emojis(text)
    text = remove_mentions(text)
    return text
async def fetch_messages3(user_id,guild_id,num):
    str = ""
    #print(user_id)
    #print(guild_id)
    #print(num)
    guild = client.get_guild(guild_id)
    channels = guild.channels
    messages = []  # 自分の投稿を保存するリスト
    days_ago = datetime.utcnow - timedelta(days=num)
    for channel in channels:
        try:
            if isinstance(channel, discord.TextChannel):
                print(f"通常のテキストチャンネル {channel.name} から取得を開始します。",flush=True)
                #await fetch_messages_from_text_channel(user_id,channel, messages)
                async for message in channel.history(after=days_ago):
                    if message.author.id == user_id:
                        messages.append(message)
            
            elif isinstance(channel, discord.ForumChannel):
                print(f"フォーラムチャンネル {channel.name} から取得を開始します。",flush=True)
                #await fetch_messages_from_forum_channel(user_id,channel, messages)
                threads = channel.threads
                for thread in threads:
                    async for message in thread.history(after=days_ago):
                        if message.author.id == user_id:
                            messages.append(message)

        except Exception as e:
            print(e,flush=True)
            #elif isinstance(channel, discord.ForumChannel):
            #    print(f"フォーラムチャンネル {channel.name} から取得を開始します。")
            #    #await fetch_messages_from_forum_channel(user_id,channel, messages)
            #    threads = channel.threads
            #    for thread in threads:
            #        async for message in thread.history(limit=100):
            #            if message.author.id == user_id:
            #                messages.append(message)

    for message in messages:
        str+=f"{message.author}: {message.content}\n"
        #print(f"{message.author}: {message.content}\n")

    #print(str)
    return str



async def fetch_messages2(user_id,guild_id,num):
    str = ""
    #print(user_id)
    #print(guild_id)
    #print(num)
    guild = client.get_guild(guild_id)
    channels = guild.channels
    messages = []  # 自分の投稿を保存するリスト
    for channel in channels:
        try:
            if isinstance(channel, discord.TextChannel):
                print(f"通常のテキストチャンネル {channel.name} から取得を開始します。",flush=True)
                #await fetch_messages_from_text_channel(user_id,channel, messages)
                async for message in channel.history(limit=100):
                    if message.author.id == user_id:
                        messages.append(message)
            
            elif isinstance(channel, discord.ForumChannel):
                print(f"フォーラムチャンネル {channel.name} から取得を開始します。",flush=True)
                #await fetch_messages_from_forum_channel(user_id,channel, messages)
                threads = channel.threads
                for thread in threads:
                    async for message in thread.history(limit=100):
                        if message.author.id == user_id:
                            messages.append(message)

        except Exception as e:
            print(e,flush=True)
            #elif isinstance(channel, discord.ForumChannel):
            #    print(f"フォーラムチャンネル {channel.name} から取得を開始します。")
            #    #await fetch_messages_from_forum_channel(user_id,channel, messages)
            #    threads = channel.threads
            #    for thread in threads:
            #        async for message in thread.history(limit=100):
            #            if message.author.id == user_id:
            #                messages.append(message)

    for message in messages:
        str+=f"{message.author}: {message.content}\n"
        #print(f"{message.author}: {message.content}\n")

    #print(str)
    return str

async def fetch_messages_from_text_channel(user_id,channel, messages):
    """通常のテキストチャンネルからメッセージを取得"""
    async for message in channel.history(limit=100):
        if message.author == user_id:
            messages.append(message)
        

async def fetch_messages_from_forum_channel(user_id,forum_channel, messages):
    """フォーラムチャンネルの各スレッドからメッセージを取得"""
    threads = forum_channel.threads
    async for message in thread.history(limit=100, before=last_message_id):
        if message.author == user_id:
            messages.append(message)


async def fetch_messages(channel_id,num):

    channel = client.get_channel(channel_id)
    if channel is None:
        print("ch not found")
        return

    one_day_ago = datetime.utcnow() - timedelta(days=1)

    messages = []
    if(num==0):
        async for message in channel.history(after=one_day_ago):
            if not message.author.bot:
                messages.append(message)
    else:
        async for message in channel.history(limit=num):
            if not message.author.bot:
                messages.append(message)
        
    str = ""
    if not messages:
        print("message not found")
        return str
    for message in messages:
        #print(f"{message.author}: {message.content}")
        str+=f"{message.author}: {message.content}\n"
    return str
    #print(g_str)
         
async def summarize(channel_id, prompt, title):
    try:
        #print("g_str")
        #print(g_str)
        channel = client.get_channel(channel_id)
        if channel is None:
            print("channel is none")
            return
        str = prompt
        #print(str)
        #model = GenerativeModel("gemini-pro")
        model = GenerativeModel("gemini-1.5-pro")
        gt = model.generate_content(str)
        #print(gt.text)
        #print(gt.candidates)
        embed = discord.Embed(
            title=title,
            description=gt.text,
            color=0x00ff00
        )
        return embed
        #await channel.send(embed=embed)
    except Exception as e:
        print(e)

@client.tree.command(name="要約", description="過去一日分のメッセージを要約します")
async def get_messages(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        str = await fetch_messages(channel_id,0)
        embed = await summarize(channel_id,"次の文章を6000字以内で要約してください：\n"+str,"要約結果")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="mvp", description="24時間のMVP")
async def mvp(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        str = await fetch_messages(channel_id,0)
        embed = await summarize(channel_id,"次の文章からMVP(最も格好良い発言)を選んでください：\n"+str,"MVP")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="今北産業", description="過去の100投稿を3行にまとめる")
async def imakita(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer()
        str = await fetch_messages(channel_id,100)
        embed = await summarize(channel_id,"次の文章を3行にまとめてください：\n"+str,"今北産業")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="silent要約", description="要約結果をあなただけにお届け")
async def silent_get_messages(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages(channel_id,0)
        embed = await summarize(channel_id,"次の文章を6000字以内で要約してください：\n"+str,"要約結果")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e) 

@client.tree.command(name="silent_mvp", description="mvpをあなただけにお届け")
async def silent_mvp(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages(channel_id,0)
        embed = await summarize(channel_id,"次の文章からMVP(最も格好良い発言)を選んでください：\n"+str,"MVP")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e) 

@client.tree.command(name="silent今北産業", description="過去の100投稿を3行にまとめてあなただけにお届け")
async def silent_imakita(interaction: discord.Interaction):
    try:
        channel_id = interaction.channel_id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages(channel_id,100)
        embed = await summarize(channel_id,"次の文章を3行にまとめてください：\n"+str,"今北産業")
        await interaction.followup.send(embed=embed)
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

@client.tree.command(name="性格分析mbti", description="過去の投稿から性格を分析")
async def mbti(interaction: discord.Interaction):
    print("mbti",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer()
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)をMBTIで分析してください：\n"+str,"MBTI")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)
    await interaction.followup.send("処理が終了しました")


@client.tree.command(name="silent性格分析mbti", description="過去の投稿から性格を分析して、あなただけにお届け")
async def silent_mbti(interaction: discord.Interaction):
    print("silent_mbti",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)をMBTIで分析してください：\n"+str,"MBTI")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)

@client.tree.command(name="性格分析big5", description="過去の投稿から性格を分析")
async def big5(interaction: discord.Interaction):
    print("big5",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer()
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)をbig5で分析してください：\n"+str,"BIG5")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="silent性格分析big5", description="過去の投稿から性格を分析して、あなただけにお届け")
async def silent_big5(interaction: discord.Interaction):
    print("silent_big5",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)をbig5で分析してください：\n"+str,"BIG5")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)

@client.tree.command(name="年齢推定", description="過去の投稿から年齢を推定")
async def age_guess(interaction: discord.Interaction):
    print("age_guess",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer()
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)から精神年齢と実年齢を推定してください：\n"+str,"年齢推定")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="silent年齢推定", description="過去の投稿から年齢を推定して、あなただけにお届け")
async def silent_age_guess(interaction: discord.Interaction):
    print("silent_age_guess",flush=True)
    try:
        user_id = interaction.user.id
        user_name = interaction.user.name
        channel_id = interaction.channel_id
        guild_id = interaction.guild.id
        await interaction.response.defer(ephemeral=True)
        str = await fetch_messages2(user_id,guild_id,1000)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の発言)から精神年齢と実年齢を推定してください：\n"+str,"年齢推定")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)

@client.tree.command(name="今日のdee", description="今日のdeeの投稿")
async def todays_dee(interaction: discord.Interaction):
    print("todays_dee",flush=True)
    try:
        user_name = "dee909.includeore"
        guild = interaction.guild  # コマンドが実行されたサーバー
        member = discord.utils.find(lambda m: m.name == user_name or m.display_name == user_name, guild.members)
        if member:
            user_id = member.id
        guild_id = interaction.guild.id
        channel_id = interaction.channel_id
        await interaction.response.defer()
        mystr = await fetch_messages3(user_id,guild_id,1)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の１日の発言)を要約してください：\n"+mystr,"今日のdee")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)
    await interaction.followup.send("処理が終了しました")

@client.tree.command(name="silent今日のdee", description="今日のdeeの投稿を要約して、あなただけにお届け")
async def silent_todays_dee(interaction: discord.Interaction):
    print("silent_todays_dee",flush=True)
    try:
        user_name = "dee909.includeore"
        guild = interaction.guild  # コマンドが実行されたサーバー
        member = discord.utils.find(lambda m: m.name == user_name or m.display_name == user_name, guild.members)
        
        if member:
            user_id = member.id
        if not member:
            await interaction.followup.send(user_name+"が見当たりません")
            return

        guild_id = interaction.guild.id
        channel_id = interaction.channel_id
        await interaction.response.defer(ephemeral=True)
        mystr = await fetch_messages3(user_id,guild_id,1)
        #print(str)
        embed = await summarize(channel_id,"次の文章("+ user_name + "の１日の発言)を要約してください：\n"+mystr,"今日のdee")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(e,flush=True)




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

        text = clean_text(text)
        text = text[:20]
        
        # Google Text-to-Speechを使って音声ファイルを生成
        tts = gTTS(text=text, lang='ja')
        tts.save("message.mp3")
        
        # ボイスチャンネルでメッセージを再生
        vc.play(discord.FFmpegPCMAudio("message.mp3",options="-filter:a atempo=2.0"), after=lambda e: print("done", e))
        
        # 再生終了を待機
        while vc.is_playing():
            await asyncio.sleep(1)

        # 一時ファイルを削除
        os.remove("message.mp3")

    except Exception as e:
        print(e)

print("client.run",flush=True)
try:
    client.run(api_token)
except Exception as e:
    print(f"Error: {e}",flush=True)
