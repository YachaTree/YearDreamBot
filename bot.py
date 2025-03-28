import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
import pytz

# .env 파일에서 환경변수 로드
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = [int(id) for id in os.getenv('CHANNEL_ID', '0').split(',')] # 메시지를 보낼 채널 ID

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 출석 체크 기록을 저장할 딕셔너리
attendance_records = {
    'check_in': {},  # 출근 체크
    'check_out': {}  # 퇴근 체크
}

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 실행되었습니다!')
    check_qr_time.start()  # QR 체크 시간 확인 작업 시작

@tasks.loop(minutes=1)  # 1분마다 체크
async def check_qr_time():
    now = datetime.datetime.now(KST)
    
    # 평일(월-금)에만 실행
    if now.weekday() < 5:  # 0=월요일, 4=금요일
        for channel_id in CHANNEL_ID:
            channel = bot.get_channel(channel_id)
            if not channel:
                continue

            # 출근 체크 알림
            if now.hour == 9 and now.minute == 0:
                await channel.send("@everyone 🌅 출석 QR 체크인 시간입니다.\n오전 9시 30분까지 꼭 QR 체크인으로 출석완료해주세요!")
            elif now.hour == 9 and now.minute == 25:
                await channel.send("@everyone ⚠️ 출석 체크인 마감 5분 전입니다!\n아직 체크인하지 않으신 분들은 서둘러주세요!")
            
            # 퇴근 체크 알림
            elif now.hour == 17 and now.minute == 30:
                await channel.send("@everyone 🌇 퇴실 QR 체크아웃 시간입니다.\n오후 6시까지 꼭 QR 체크아웃 해주세요!")
            elif now.hour == 17 and now.minute == 55:
                await channel.send("@everyone ⚠️ 퇴실 체크아웃 마감 5분 전입니다!\n아직 체크아웃하지 않으신 분들은 서둘러주세요!")

@bot.command(name='출석')
async def check_in(ctx):
    user_id = ctx.author.id
    current_date = datetime.datetime.now(KST).date()
    
    if user_id not in attendance_records['check_in']:
        attendance_records['check_in'][user_id] = []
    
    if current_date in attendance_records['check_in'][user_id]:
        await ctx.send(f'{ctx.author.mention}님은 이미 오늘 출석 체크를 하셨습니다!')
        return
    
    attendance_records['check_in'][user_id].append(current_date)
    await ctx.send(f'{ctx.author.mention}님 출석 체크 완료!')

@bot.command(name='퇴실')
async def check_out(ctx):
    user_id = ctx.author.id
    current_date = datetime.datetime.now(KST).date()
    
    if user_id not in attendance_records['check_out']:
        attendance_records['check_out'][user_id] = []
    
    if current_date in attendance_records['check_out'][user_id]:
        await ctx.send(f'{ctx.author.mention}님은 이미 오늘 퇴실 체크를 하셨습니다!')
        return
    
    attendance_records['check_out'][user_id].append(current_date)
    await ctx.send(f'{ctx.author.mention}님 퇴실 체크 완료! 수고하셨습니다! 🎉')

@bot.command(name='출석확인')
async def check_in_status(ctx):
    user_id = ctx.author.id
    current_date = datetime.datetime.now(KST).date()
    
    check_in_done = user_id in attendance_records['check_in'] and current_date in attendance_records['check_in'][user_id]
    check_out_done = user_id in attendance_records['check_out'] and current_date in attendance_records['check_out'][user_id]
    
    status_message = f'{ctx.author.mention}님의 오늘 출퇴근 현황:\n'
    status_message += f'- 출석 체크: {"✅ 완료" if check_in_done else "❌ 미완료"}\n'
    status_message += f'- 퇴실 체크: {"✅ 완료" if check_out_done else "❌ 미완료"}'
    
    await ctx.send(status_message)

@bot.command(name='서버목록')
async def list_servers(ctx):
    servers = bot.guilds
    message = "봇이 참여중인 서버 목록:\n"
    for server in servers:
        message += f"- {server.name}\n"
    await ctx.send(message)

# 봇 실행
bot.run(TOKEN) 