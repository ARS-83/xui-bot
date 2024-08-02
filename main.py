import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup
from pyromod.helpers import ikb, array_chunk
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pyromod
import datetime
import base64
import jdatetime
import aiofiles

import configparser

from  uuid import uuid4
import httpx
import sqlite3      
import time
import os


config = configparser.ConfigParser()
config.read('config.ini')



app = Client("ARS_God", 
             api_id=config.get('GENERAL','api_id'),
        
             api_hash=config.get('GENERAL','api_hash'),                                                                                               
             bot_token=config.get('GENERAL','bot_token')
             )


#  ps aux | grep python3


async def CheckState(_,c:Client,m:Message):

 context.execute('SELECT State FROM ManageBot ')
 data = context.fetchone()
 
 if data[0] == 1 :
    return True
 else:
      if CheckAdmin(m.from_user.id)[1] == True:return True
          
      await m.reply("❤️‍🔥 بات در حال حاضر خاموش است کمی منتظر بمانید ")
      return False

     



Check_State = filters.create(CheckState)

db = sqlite3.connect("db/ARS.db")
context = db.cursor()

def readfils():
    try:
        file = open("config.json", "r")
        config = json.loads(file.read())
        file.close()
        return config[0]
    except Exception as e:
        print(e)
  
async def ReadFileConfig():
   async with aiofiles.open('config.json', mode='r',encoding='utf-8') as f: 
      res =   json.loads(await f.read())
   return res   

async def SaveFileConfig(data):
 async with aiofiles.open('config.json', mode='w',encoding='utf-8') as f: 
      await f.write(json.dumps(data))



async def SendAlert():
 
    
    context.execute("SELECT * FROM Servers;")
    
    servers =context.fetchall()
    context.execute("SELECT Time,Total FROM ManageBot;")
    Setting = context.fetchone()


    for server in servers:
            
         origin= server[1].split("/")
         headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate',
  'X-Requested-With': 'XMLHttpRequest',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': f'{origin[0]}://{origin[2]}',
  'Connection': 'keep-alive',
  'Referer': f'{server[1]}/panel/inbounds',
  'Cookie': ''
}

         async with httpx.AsyncClient() as clienthttp:
          try:

             response =  await clienthttp.post(url=f"{server[1]}/login",data={"username":f"{server[3]}","password":f"{server[4]}"})
          
             session = response.headers.get("Set-Cookie").split("; ")[0]   
             headers['Cookie']  = f"lang=en-US; {session}"
             response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
          except:
           response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
         info_json = json.loads(response.text)
         inbounds = info_json["obj"]
         
         for inbound in inbounds:
            
            settings = json.loads(inbound['settings'])
            for client in settings['clients']:
                uuid = ""
                if inbound["protocol"] == "trojan":
                 uuid = client['password']
                else:
                 uuid = client['id']
                 context.execute(f"SELECT userId,Alert,FinalAlert,proof FROM UserConfig WHERE uuid = '{uuid}' ") 
              
                GetUsers =  context.fetchall()
         
                for GetUser in GetUsers:
                 if GetUser != None:
                   if GetUser[1]!= 1:
                    Alerted = False
                    proof = ""
                    mes = f"⚠️ 1اشتراک شما رو به تمام است. ⚠️\n\nمشترک گرامی: {client['email']}"
                    if client['expiryTime'] != 0:
                     date  = ""
                     if 0 < client["expiryTime"]:
 
                                date = datetime.datetime.fromtimestamp(
                                    client["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                                toEnd = date - datetime.datetime.now(tz=datetime.timezone.utc)
                                if   0 < toEnd.days  <  Setting[0]  :
                                       Alerted =True
                                       mes += f"\nکمتر از  { Setting[0]}  روز از اشتراک شما باقی مانده است.\n\nدر صورت تمایل،قبل از قطع شدن اتصال،هر چه سریع تر توسط نمایندگان فروش،اشتراک خود را تمدید کنید. "
                                       proof = "date" 
                 
                                elif toEnd.days == 0 and  toEnd.seconds > 0 :
                                       Alerted =True
                                       mes += f"\nکمتر از  { Setting[0]}  روز از اشتراک شما باقی مانده است.\n\nدر صورت تمایل،قبل از قطع شدن اتصال،هر چه سریع تر توسط نمایندگان فروش،اشتراک خود را تمدید کنید. "
                                       proof = "date"
                    if client['totalGB'] !=0:
                     
                      res =round(client['totalGB'] / (1024 * 1024 * 1024), 2) 
                      if res < Setting[1]:
                        mes += f"""\nکمتر از  { Setting[1]}  گیگ از حجم اشتراک شما باقی مانده است.\n\nدر صورت تمایل،قبل از قطع شدن اتصال،هر چه سریع تر توسط نمایندگان فروش،اشتراک خود را تمدید کنید."""
                        proof += "_volume"
                        Alerted = True
                    if Alerted ==True   :
                         #   mes+= f"""
                      
#{client['email']} : نام اشتراک 

#🔰 /start 
#"""
                            await app.send_message(chat_id= int(GetUser[0]),text =mes)
                            context.execute(f"UPDATE UserConfig SET Alert = 1,proof ='{proof}'  WHERE uuid = '{uuid}'")
                            db.commit()
                   else:
                    mes =f"""⚠️ مشترک گرامی: {client['email']}"""
                    if GetUser[3]  ==  "date_volume":
                       
                       date = datetime.datetime.fromtimestamp(
                       client["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                       toEnd = date - datetime.datetime.now(tz=datetime.timezone.utc)
                       if round(client['totalGB'] / (1024 * 1024 * 1024), 2) > Setting[1] and toEnd.days > Setting[0]  :
                           

                           context.execute(f"UPDATE UserConfig SET FinalAlert = 0,Alert = 0, proof = 'empty' WHERE uuid = '{uuid}'")
                           db.commit()
                           
                       else:
                           if  GetUser[2] == 0:
                            
                            alert = False
                            if client['expiryTime'] != 0:
                              date  = ""
                              if 0 < client["expiryTime"]:
 
                                date = datetime.datetime.fromtimestamp(
                                    client["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                                toEnd = date - datetime.datetime.now(tz=datetime.timezone.utc)
                                if    toEnd.days <=  0  :
                                      
                                       mes += f"""⛔️ اشتراک شما به پایان رسید ⛔️
اشتراک شما به دلیل اتمام روز به پایان رسید و اتصال شما قطع شد.

در صورت تمایل،میتوانید توسط نمایندگان فروش،اشتراک خود را تمدید کنید.
"""
                                       alert   =True

                                
                            if round(client['totalGB'] / (1024 * 1024 * 1024), 2) < 0.2:
                                mes += """ ⚠️ کاربر گرامی ؛تا لحظاتی دیگر اشتراک شما به دلیل اتمام حجم به پایان میرسد و اتصال شما قطع خواهد شد.

در صورت تمایل،قبل از قطع شدن اتصال،هر چه سریع تر توسط نمایندگان فروش،اشتراک خود را تمدید کنید.
"""
                                alert = True
                            if  alert ==True:

                                await app.send_message(chat_id= int(GetUser[0]),text =mes)
                                context.execute(f"UPDATE UserConfig SET FinalAlert = 1 WHERE uuid = '{uuid}'")
                                db.commit()

                    elif "date" in GetUser[3]:
                      if  GetUser[2] == 0: 
                       date = datetime.datetime.fromtimestamp(
                       client["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                       toEnd = date - datetime.datetime.now(tz=datetime.timezone.utc)

                       if   toEnd.days > Setting[0]  :
                            context.execute(f"UPDATE UserConfig SET FinalAlert = 0,Alert = 0, proof = 'empty' WHERE uuid = '{uuid}'")
                            db.commit()
                       elif  toEnd.days <=  0 :
                            mes += """⛔️ اشتراک شما به پایان رسید ⛔️
اشتراک شما به دلیل اتمام روز به پایان رسید و اتصال شما قطع شد.

در صورت تمایل،میتوانید توسط نمایندگان فروش،اشتراک خود را تمدید کنید.
"""
                            

                            await app.send_message(chat_id= int(GetUser[0]),text =mes)
                            context.execute(f"UPDATE UserConfig SET FinalAlert = 1 WHERE uuid = '{uuid}'")
                            db.commit()
                    elif GetUser[3]== "_volume"  :   
                        if  GetUser[2] == 0:  
                          if round(client['totalGB'] / (1024 * 1024 * 1024), 2) > Setting[1]  :
                           

                            context.execute(f"UPDATE UserConfig SET FinalAlert = 0,Alert = 0, proof = 'empty' WHERE uuid = '{uuid}'")
                            db.commit()
                          else:
                            mes += """ ⚠️ کاربر گرامی ؛تا لحظاتی دیگر اشتراک شما به دلیل اتمام حجم به پایان میرسد و اتصال شما قطع خواهد شد.

در صورت تمایل،قبل از قطع شدن اتصال،هر چه سریع تر توسط نمایندگان فروش،اشتراک خود را تمدید کنید.
"""
                            

                            await app.send_message(chat_id= int(GetUser[0]),text =mes)
                            context.execute(f"UPDATE UserConfig SET FinalAlert = 1 WHERE uuid = '{uuid}'")
                            db.commit()

                           
                           
                           
                           
                           

                           



 

                           
                           
                     
                         
                         
                           
                           
                     

            #     if inbound["protocol"] == "trojan":
            #         if trojan == True:
            #             if uuid == client['password']:
            #                 email = client['email']
            #                 break

            #     else:
            #         if uuid == client['id']:
            #             email = client['email']
            #             break

            # if email != "":
            #     print("test")
            #     states = inbound['clientStats']
            #     print(states)
            #     for state in states:
            #         if state["email"] == email:

 

async def sendMessage():
 data =await ReadFileConfig()
 if data[0]['SendingPublicMessage'] == 0:
 
 
  context.execute("SELECT * FROM PublicMessage WHERE IsSended = 0 AND IsDelete = 0")
  pm=  context.fetchone()
  if pm != None:
    data[0]['SendingPublicMessage'] = 1
    await SaveFileConfig(data)
    await app.send_message(pm[6] , f"🔔 شروع ارسال پیام {pm[1]}")
    context.execute("SELECT uuid FROM Users")
    Users =  context.fetchall()
    counter  =pm[3]
    for user in Users:
      checkMes =  context.execute(f"SELECT IsDelete FROM PublicMessage WHERE Id = {pm[0]}")
      checkMes =  context.fetchone()
      if checkMes[0] == 0:
        time.sleep(0.5)
       
        try:

         await app.send_message(chat_id= user[0] ,text= f""" عنوان :{pm[1]} 
{pm[2]}

""" )
        except:
            print("""A User CanNot Send Message 
Why?
1- User Not Block Bot 
2- User Not Start This Token Bot                
                  """)
        counter += 1
        context.execute(f"UPDATE PublicMessage SET CountSended = { counter } WHERE Id = {pm[0]}")
        db.commit()
    context.execute(f"UPDATE PublicMessage SET IsSended = 1 WHERE Id = {pm[0]}")  
    db.commit()
    data[0]['SendingPublicMessage'] = 0
    await SaveFileConfig(data)

 
  return

# TODO ADD MES CHANEL AND LOGETTIC Qure KESHi
# async def UpdateCookie():
#  try:
#     db = await aiosqlite.connect("db/ARS.db")
#     context  = await db.cursor()
#     await context.execute("SELECT * FROM Servers;")
    
#     servers =await context.fetchall()
   

#     for server in servers:
                     
#                  async with httpx.AsyncClient() as clienthttp:
#                     res =await clienthttp.post(
#                      f"{server[1]}/login", data=f"username={server[3]}&password={server[4]}", headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=8)

#                  if res.status_code == 200:
#                      current_session = res.headers.get(
#                     "Set-Cookie").split("; ")[0]
#                      await context.execute(f"UPDATE Servers SET Session = '{current_session}' WHERE serverId = {server[0]}")
#                      await db.commit()
 
#     await context.close() 
#     await db.close()
#     return
#  except :
#                      adminId =await ReadFileConfig()[0]['admin']
#                      await app.send_message(chat_id=adminId,text=f"هنگام به روز رسانی کوکی سرور {server[2]} به مشکل خوردیم")
#                      await context.close() 
#                      await db.close()
#                      return

async def SendBackUp():
#   try:
 
    context.execute("SELECT Chanel FROM ManageBot  ")
    chanel =   context.fetchone()
    await app.send_document(f"{chanel[0]}","db/ARS.db")

    

    context.execute("SELECT * FROM Servers;")
    
    servers = context.fetchall()
   

    for server in servers:
       try:       
                 origin= server[1].split("/")
                 headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate',
  'X-Requested-With': 'XMLHttpRequest',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': f'{origin[0]}://{origin[2]}',
  'Connection': 'keep-alive',
  'Referer': f'{server[1]}/panel/inbounds',
  'Cookie': ''
}
                 res = None       
                 async with httpx.AsyncClient() as clienthttp:
                    response =  await clienthttp.post(url=f"{server[1]}/login",data={"username":f"{server[3]}","password":f"{server[4]}"})
          
                    session = response.headers.get("Set-Cookie").split("; ")[0]   
                    headers['Cookie']  = f"lang=en-US; {session}"
                    res =await clienthttp.get(server[1] + "/server/getDb", headers=headers, timeout=6)
                 file = open(f"backUp/x-ui.db","wb")
                 file.write(res.content)
                 file.close()
                
                 await app.send_document(f"{chanel[0]}",document='backUp/x-ui.db',caption=f"بکاپ پنل {server[2]}")

                 os.remove('backUp/x-ui.db')   
       except :
                     adminId =await ReadFileConfig()[0]['admin']
                     await app.send_message(chat_id=adminId,text=f"هنگام دریافت بکاپ  سرور {server[2]} به مشکل خوردیم")

    return                     
#   except:
#        adminId =await ReadFileConfig()
#        adminId = adminId[0]['admin']
#        await app.send_message(chat_id=adminId,text=f" لطفا بات را در چنل بکاپ ادد کنید با تشکر")
#        await context.close() 
#        await db.close()
#        return

scheduler = AsyncIOScheduler()
scheduler.add_job(sendMessage, "interval",seconds=300)
scheduler.add_job(SendAlert, "interval",seconds=300)
# scheduler.add_job(UpdateCookie, "interval",seconds=3600)
scheduler.add_job(SendBackUp, "interval",seconds=3600)

def AddServerToConf(u: str, name: str, p: str, url: str, s: str,typeServer:str):



    try:
        context.execute(f"""INSERT INTO Servers(Url, Name, UserName, Pass,Session,TypeServer) 
   VALUES('{url}', '{name}', '{u}', '{p}', '{s}','{'sanaei' if typeServer == 'sanaei' else 'alireza'}');""")
        db.commit()
      
        returnData= True
        return returnData
    except:
        return False 


def Tree():
    return defaultdict(Tree)


    
    
    
back_btn = InlineKeyboardMarkup(
    [[InlineKeyboardButton("بازگشت 🔙", callback_data="ServersList")]])
user_pack = Tree()
btn_Reply = ReplyKeyboardMarkup([["اکانت های من 👤","📋 استعلام اکانت" ]],
                                resize_keyboard=True, one_time_keyboard=True)
btn_Reply_admin = ReplyKeyboardMarkup([["اکانت های من 👤","📋 استعلام اکانت"],["🔨 مدیریت ربات"]],
                                      resize_keyboard=True, one_time_keyboard=True)



def convert_link_vmess(vmess_account: str):
    try:
        base64_content = vmess_account[8:]
        base64_bytes = base64_content.encode("ascii")

        sample_string_bytes = base64.b64decode(base64_bytes)
        sample_string = sample_string_bytes.decode("ascii")
        x = sample_string.replace("\'", "\"")
        if "b{" in str(x):
          x= x[1:]
        return json.loads(str(x))["id"]
  
    except:
        return "configKosSher"
    
def wings(vmess_account: str):
    base64_content = vmess_account[8:]
    base64_decoded_content = base64.b64decode(
        base64_content.encode('utf-8')).decode('utf-8', 'ignore')
    return json.loads(base64_decoded_content)

def chackState():
     
      context.execute(f"SELECT * FROM ManageBot;")
      set= context.fetchone()
      return set[1]
def convert_link_vless(vless_account: str):
    content = vless_account[8:]
    id = content.split("@")[0]
    return id
def CheckServer(srId:int):
      context.execute(f"SELECT * FROM Servers WHERE serverId={srId};")
      server= context.fetchone()
      if server!=None:
          return True
      else :
          return False

def FindTrojanPass(conf: str):
    content = conf[9:]
    return content.split("@")[0]
def CheckBlock(userId:int):
      context.execute(f"SELECT * FROM Users WHERE uuid='{userId}';")
      user = context.fetchone()
      if user==None:
          return False
      else:
          if user[2]==1:
              return True
          else:
              return False
    
async def GetMain(call:CallbackQuery):
        if CheckAdmin(call.from_user.id)[0] or CheckAdmin(call.from_user.id)[1]:
            await call.message.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply_admin)
        else:    
            await call.message.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply)
def CheckAdmin(userId:int):
   
     context.execute(f"SELECT * FROM Users WHERE uuid={userId};")
     user= context.fetchone()
    
     if user==None:
         return [False,False] 
     elif user[3]==1:
        if readfils()["admin"] == userId:
         return [True,True]
        else:
            return [True,False] 
     elif user[3]==0:
             return [False,False] 

@app.on_message(filters.regex("🔨 مدیریت ربات") & ~ filters.command("start"))
async def ManageBot(c:app,m:Message):

 if CheckBlock(m.from_user.id)==False:
   if CheckAdmin(m.from_user.id)[0] == True:
      
              await m.reply(f"🔰 | سلام  {m.from_user.first_name} \n\n به بخش مدیریت ربات خود خوش آمدید \n میتوانید از منوی زیر انتخاب کنید 👇🏻 \n\n▪️▫️▪️▫️▪️▫️▪️▫️▪️",reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton("لیست سرور ها",callback_data="ServersList"),InlineKeyboardButton("افزودن سرور",callback_data="AddServer")],[InlineKeyboardButton("مدیریت کاربران",callback_data="manageUser"),InlineKeyboardButton("آمار ربات",callback_data="Amar")],[InlineKeyboardButton("مدیریت ربات",callback_data="manageBot")]]))
   else:
      await m.reply("کاربرگرامی شما از سوی ادمین مسدود شده اید")        
 else :
     await m.reply("کاربر گرامی شما مسدود شده اید لطفا با پیام به پشتیبانی پیگیری کنید")
         
    
@app.on_message(filters.regex("adddb") & ~ filters.command("start"))
async def listAccount(m:Message,c:app):
    
#         context.execute("""CREATE TABLE IF NOT EXISTS Users(
#    userId INTEGER PRIMARY KEY AUTOINCREMENT,
#    uuid INT,
#    IsBlock INT,
#    ISAdmin INT,
#    Name TEXT
#    );
# """)
   context.execute("""CREATE TABLE IF NOT EXISTS UserConfig(
    configId INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT,
    userId TEXT,
    email TEXT,
    Alert INT,
    ServerName TEXT,
    serverId INT
    );
 """)
# #    context.execute("""CREATE TABLE IF NOT EXISTS ManageBot(
#    Id INTEGER PRIMARY KEY AUTOINCREMENT,
#    State INT,
#    NewConf INT,
#    Time INT,
#    Total INT,
#    Chanel TEXT
#    );
# """)
#    context.execute(f"""INSERT INTO ManageBot(State, NewConf, Time, Total, Chanel) 
#    VALUES( 1, 1, 1, 1, 'ARSISGod');""")
   db.commit()

        
    #  except:
    #      m.reply("اکانتی یافت نشد لطفا از قسمت مشخصات کانفیگ کانفیگ خود را اضافه کنید")      
# async def SendAlert(c:app):
#      email = ""
#      enable = ""
#      up = None
#      addToDate=""
#      down = None
#      expiryTime = None
#      total = None
#      allow = False
#      startUse =""
#      trojan = False
#      jalili_date = None
#      consumption = None
#      uuid =""
#      remaining = None
#      email=""
#      while True:
        
        
        
       
                          
#       await time.sleep(1000) 
     
#       await context.execute(f"SELECT * FROM Servers;")
#       servers=await context.fetchall()
#       await context.execute(f"SELECT * FROM UserConfig")
#       confD=await context.fetchall()
  
#       for server in servers:
#         try:
#           try:
#                   res =await requests.post(
#                 f"{server[1]}/login", data=f"username={server[3]}&password={server[4]}", headers={'Content-Type': 'application/x-www-form-urlencoded'})

#                   if res.ok:
                      
#                       current_session =await res.headers.get(
#                     "Set-Cookie").split("; ")[0]
                   
#                       response = await requests.post(server[1] + "/panel/inbound/list", headers={
#                     "cookie": f"{current_session}"}).text
#           except:
#               try:
#                    response = await requests.post(server[1] + "/panel/inbound/list", headers={
#                 "cookie": f"{current_session}"}).text    
#               except:
#                  print("Error To Get Data .....")    
       
#           info_json =await json.loads(response)
#           inbounds =await info_json["obj"]
       
#           for inbound in inbounds:
#             # print(inbound)
#             if email != "":
#                 break
#             settings =await json.loads(inbound['settings'])
      
#             for client in settings['clients']:
#                 if inbound["protocol"] == "trojan":
#                     if trojan == True:
#                             uuid =await client['password']
#                             email =await client['email']
#                             break

#                 else:
#                     if uuid == client['id']:
#                         email =await client['email']
#                         break

#             if email != "":
               
#                 states = inbound['clientStats']
#                 for state in states:
#                     if state["email"] == email:

                     
                  
#         except:
#           file =await open("config.json", "r")
#           config =await json.loads(file.read())
#           await file.close()    
#           await c.send_message(config[0]["admin"],f"ادمین گرامی هنگام درخواست به سرور   {server[2]} مشکلی پیش آمده ممکن است اعتبار سشن به پایان رسیده یا اطلاعات سرور به درستی وارد نشده باشد")


async def CheckBtnsNot(_,c:Client,m:Message):
   btns =["اکانت های من 👤","📋 استعلام اکانت","🔨 مدیریت ربات","/start"]

   if m.text not in btns : 
       
       return True
   else:
        context.execute(f"UPDATE Users SET STEP = 'home' WHERE userId = {m.from_user.id}")
        db.commit()
       
        return False


checkbtns = filters.create(CheckBtnsNot)

@app.on_message(checkbtns)

async def STEPManager(c:app,m:Message):

    context.execute(f'SELECT  STEP FROM Users WHERE uuid = {m.from_user.id}')
    STEP = context.fetchone()
    print(m.from_user.id)
    if m.text == 'انصراف':
              context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
              db.commit()
              try:
                   context.execute(f"SELECT * FROM Users WHERE uuid={m.from_user.id};")
                   user= context.fetchone()
      
        
                   if user==None :
                      if readfils()["admin"] ==  m.from_user.id:
                              await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply_admin)
                
                              context.execute(f"""INSERT INTO Users(uuid, IsBlock, ISAdmin, Name,STEP) 
   VALUES('{m.from_user.id}', 0, 1, '{m.from_user.username}','home');""")
                              db.commit()
                              return
                      else:
                
                       await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply)
                       
                       context.execute(f"""INSERT INTO Users(uuid, IsBlock, ISAdmin, Name,STEP) 
   VALUES('{m.from_user.id}', 0, 0, '{m.from_user.username}','home');""")
                       db.commit()
                       return
                   elif user[3]==0:
                    if user[2]==1:
                      await m.reply("کاربر گرامی شما مسدود شده اید لطفا از طریق پشتیبانی پیگیری کنید")
                      context.execute(f"""UPDATE Users SET STEP = 'home' WHERE uuid = '{m.from_user.id}'""")
                      db.commit()
                       
                      return
                    await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply)
                    context.execute(f"""UPDATE Users SET STEP = 'home' WHERE uuid = '{m.from_user.id}'""")
                    db.commit()
                    
                    return
                   elif user[3]==1:
                       if user[2]==1:
                         await m.reply("کاربر گرامی شما مسدود شده اید لطفا از طریق پشتیبانی پیگیری کنید")
                         context.execute(f"""UPDATE Users SET STEP = 'home' WHERE uuid = '{m.from_user.id}'""")
                         db.commit()
                       
                         return
                       await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply_admin)
                       context.execute(f"""UPDATE Users SET STEP = 'home' WHERE uuid = '{m.from_user.id}'""")
                       db.commit()
                       return
              except:
                    await m.reply(f"تنظیمات بات به درستی اعمال نشده ")
                    return
       
    if STEP[0] == 'addapp' :
     servers = []
     context.execute("SELECT * FROM Servers;")
     servers.append(context.fetchall())
   
     if servers != [None]:
       uuid = 0
       email = ""
       allow = False
       trojan = False
       startUse = ""
       addToDate = ""
       jalili_date =""
       if m.text.strip().startswith("vless://"):
           await m.reply("🕒 لطفا کمی صبر کنید...")
           uuid = convert_link_vless(m.text)
       elif m.text.strip().startswith("vmess://"):
        
            uuid = convert_link_vmess(m.text)
            if uuid=="configKosSher":
              await m.reply("⚠ کانفیگ را به صورت کامل وارد کنید")
              context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
              db.commit()
       
              return
            else:
             await m.reply("🕒 لطفا کمی صبر کنید...")
        
       elif m.text.strip().startswith("trojan://"):
            await m.reply("🕒 لطفا کمی صبر کنید...")
            uuid = FindTrojanPass(m.text)
            trojan = True
       elif "vnext" in m.text:
         await m.reply("🕒 لطفا کمی صبر کنید...")
         details = json.loads(m.text)
        
         if details["outbounds"][0]["protocol"] == "trojan":
            trojan = True
         uuid = details["outbounds"][0]["settings"]["vnext"][0]["users"][0]["id"]
       elif m.text.strip().startswith("wings://"):
        await m.reply("🕒 لطفا کمی صبر کنید...")
        data = wings(m.text)
        
        if data["outbound"]["protocol"] == "trojan":
            trojan = True
            uuid = data["outbound"]["uuid"]
       else:
           await m.reply("🕒 لطفا کمی صبر کنید...")

           uuid = m.text
       context.execute(f"SELECT * FROM UserConfig WHERE uuid='{uuid}' AND userId = '{m.from_user.id}';")
       userconf= context.fetchone()

       if not userconf == None:
                    await m.reply("⚠️ این کانفیگ را قبلا یکبار استعلام گرفته اید و در لیست اکانت های من ذخیره شده است. \n\n 👈 جهت استعلام اکانت،ابتدا روی (  /start ) کلیک کنید و در منوی زیر روی گزینه (👤اکانت های من) و سپس اکانت مورد نظر کلیک کنید تا مانده حجم و روز اکانت خود را دریافت کنید و دیگر نیاز به ارسال کانفیگ نیست.\n\n")
                    context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
                    db.commit()
       
                    return
       for server in servers[0]:
            
         if email != "":
            break
           
         origin= server[1].split("/")
         headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate',
  'X-Requested-With': 'XMLHttpRequest',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': f'{origin[0]}://{origin[2]}',
  'Connection': 'keep-alive',
  'Referer': f'{server[1]}/panel/inbounds',
  'Cookie': ''
}

         async with httpx.AsyncClient() as clienthttp:
          try:

             response =  await clienthttp.post(url=f"{server[1]}/login",data={"username":f"{server[3]}","password":f"{server[4]}"})
          
             session = response.headers.get("Set-Cookie").split("; ")[0]   
             headers['Cookie']  = f"lang=en-US; {session}"
             response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
          except:
           response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
         info_json = json.loads(response.text)
          
          
      
         inbounds = info_json["obj"]
         
         for inbound in inbounds:
            if email != "":
                break
            settings = json.loads(inbound['settings'])
            for client in settings['clients']:
                if inbound["protocol"] == "trojan":
                    if trojan == True:
                        if uuid == client['password']:
                            email = client['email']
                            break

                else:
                    if uuid == client['id']:
                        email = client['email']
                        break

            if email != "":
                print("test")
                states = inbound['clientStats']
            
                for state in states:
                    if state["email"] == email:
                          
                         total = str(
                            round(state['total'] / (1024 * 1024 * 1024), 2))+" GB"
                         up = round(state['up'] / (1024 * 1024 * 1024), 2)
                         down = round(state['down'] / (1024 * 1024 * 1024), 2)
                         if total == "0.0 GB":
                            total = "نامحدود"
                            remaining = "نامحدود"
                         else:
                            remaining = round(round(state['total'] / (1024 * 1024 * 1024), 2) - (up + down),2)

                       
                         consumption = str(round(down + up,2)) + "GB"
                         if state["enable"] == True:
                            enable = "فعال 🟢"

                         elif state["enable"] == False:
                            enable = "غیرفعال 🔴"

                         if state["expiryTime"] != 0:
                            if 0 > state["expiryTime"]:
                                if down + up == 0.0:
                                    startUse = "-شروع نشده-" 
                                mili = str(state["expiryTime"])[1:]
                                if int( round((int(mili)/86400000), 2)) < 1:
                                     addToDate +=  "کمتر از یک رو از اشتراک شما باقی مانده"
                                else:
                                    addToDate += "روز های باقی مانده"
                                    
                                mili = str(state["expiryTime"])[1:]
                                if int( round((int(mili)/86400000), 2)) < 1:
                                   jalili_date = ""
                               # else:
                                     #jalili_date = int(
                                    #round((int(mili)/86400000), 2))
                            else:
                                expiryTime = datetime.datetime.fromtimestamp(
                                    state["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                                jalili_date = jdatetime.datetime.fromgregorian(day=expiryTime.day, month=expiryTime.month, year=expiryTime.year, hour=expiryTime.hour, minute=expiryTime.minute, second=expiryTime.second)
            
                               
                         elif state["expiryTime"] == 0:
                            jalili_date = "نامحدود"
                        
                      
                            
                         await m.reply(f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse } {str(jalili_date)} \n🌐 سرور: {server[2]}\n\n ▪️▫️▪️▫️▪️▫️▪️▫️▪️")
                         context.execute(f"""INSERT INTO UserConfig(uuid, userId, email, Alert, ServerName, serverId)
                            VALUES('{uuid}', '{m.from_user.id}', '{email}', 0,'{server[2]}', {server[0]});""")
                         db.commit()
                         allow = True
                         await m.reply("✅ کانفیگ شما با موفقیت به لیست اکانت های شما اضافه شد. \n\n 👈 جهت مشاهده مانده حجم یا روز اکانت خود،ابتدا روی (  /start ) کلیک کنید و در منوی زیر روی گزینه (👤اکانت های من) و سپس اکانت مورد نظر کلیک کنید تا مانده حجم و روز اکانت خود را دریافت کنید و دیگر نیاز به ارسال کانفیگ نیست.\n\n ")
                         context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
                         db.commit()
       
       if allow ==False:
           await m.reply("متاسفانه کانفیگ پیدا نشد")    
           context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
           db.commit()
                       
    else :
        context.execute(f"UPDATE Users SET STEP = 'home' WHERE uuid = {m.from_user.id}")
        db.commit()
       
    



@app.on_message(filters.regex("runChecker") & ~ filters.command("start"))
async def A_God(c: app, m: Message):
  print(m.from_user.id)
  if  m.from_user.id == readfils()["admin"]:  
      await SendAlert(app)

@app.on_message(filters.command("start") & Check_State   )
async def A_God(c: app, m: Message):
     try:
        context.execute(f"SELECT * FROM Users WHERE uuid={m.from_user.id};")
        user= context.fetchone()
      
        
        if user==None :
            if readfils()["admin"] ==  m.from_user.id:
                 await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply_admin)
                
                 context.execute(f"""INSERT INTO Users(uuid, IsBlock, ISAdmin, Name,STEP) 
   VALUES('{m.from_user.id}', 0, 1, '{m.from_user.username}','home');""")
                 db.commit()
            else:
                
             await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply)
                    
             context.execute(f"""INSERT INTO Users(uuid, IsBlock, ISAdmin, Name,STEP) 
   VALUES('{m.from_user.id}', 0, 0, '{m.from_user.username}','home');""")
             db.commit()
        elif user[3]==0:
            if user[2]==1:
                await m.reply("کاربر گرامی شما مسدود شده اید لطفا از طریق پشتیبانی پیگیری کنید")
                return
            await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply)
            
        elif user[3]==1:
            if user[2]==1:
                await m.reply("کاربر گرامی شما مسدود شده اید لطفا از طریق پشتیبانی پیگیری کنید")
                return
            await m.reply(f"به ربات استعلام خوش آمدید 🖐 \n \nجهت دریافت کانفیک آپدیت شده ویا استعلام از مانده حجم یا زمان اکانت خود،ابتدا از منوی زیر دکمه استعلام اکانت را انتخاب و سپس کانفیگ را از اکانت خود کپی و به صورت کامل ارسال کنید.", reply_markup=btn_Reply_admin)
     except:
        await m.reply(f"تنظیمات بات به درستی اعمال نشده ")

@app.on_message(filters.regex("📋 استعلام اکانت") & ~ filters.command("start") & Check_State   )
async def AddAccounnt(client: app, m: Message):
 if chackState()==0 & CheckAdmin(m.from_user.id)[0]==False:
     await m.reply("بات در حال حاضر خاموش میباشد لطفا بعدا تلاش کنید")
     return
 if CheckBlock(m.from_user.id)==False:
        
   
    # answer = await m.chat.ask('کانفیگ را از اکانت خود کپی کنید و ارسال کنید:')    
    context.execute(f"UPDATE Users SET STEP = 'addapp' WHERE uuid = {m.from_user.id}")
    db.commit()
    await m.reply('کانفیگ را از اکانت خود کپی کنید و ارسال کنید:',reply_markup=ReplyKeyboardMarkup([['انصراف']],resize_keyboard=True))
    return
 else:
      await m.reply("کاربرگرامی شما از سوی ادمین مسدود شده اید")
@app.on_message(filters.regex("اکانت های من 👤") & ~ filters.command("start") & Check_State )       

async def UserConfig(c: app, m: Message):
    if chackState()==0 & CheckAdmin(m.from_user.id)[0]==False:
        await m.reply("بات در حال حاضر خاموش میباشد لطفا بعدا تلاش کنید")
        return
    if CheckBlock(m.from_user.id)==False:
      
      context.execute(f"SELECT * FROM UserConfig WHERE userId = '{m.from_user.id}';")
      userconf= context.fetchall()
      btns=[]
      if userconf==[]:
          await m.reply("⚠️ شما اکانت ثبت شده ای ندارد. \n\n ابتدا روی (/start) کلیک کنید و از منوی زیر گزینه استعلام اکانت را انتخاب کنید و کانفیگ را از اکانت خود کپی و ارسال کنید تا اکانتتان در این لیست ثبت شود.")
          
      else:
          for conf in userconf:
           btns.append((conf[3],f"ARSShowConf_{conf[0]}"))
           btns.append(("❌",f"DeleteUserConf_{conf[0]}"))
          await m.reply("👤 | لیست اکانت های شما \n\n جهت استعلام،اکانت مورد نظر خود را از لیست زیر انتخاب کنید🔻:", reply_markup=ikb(array_chunk(btns,2)))    
    else:
      await m.reply("کاربرگرامی شما از سوی ادمین مسدود شده اید")       
      
def GetConfig(stream: str, uuid: str, email: str, port: str, protocol: str, serverName: str, remark:str):
    # Your Remark
    inboundSetting = json.loads(stream)
 


    path = None
    host = "none"
    domainName = None
    serviceName = None
    headerType = None
    alpn = None
    kcpType = None
    grpcSecurity = None
    netType = inboundSetting["network"]
    tls = inboundSetting["security"]
   
    if tls == "tls":
        domainName = inboundSetting["tlsSettings"]["serverName"]
    elif tls == "xtls":
        domainName = inboundSetting["xtlsSettings"]["serverName"]
    if netType == "grpc":
        if (tls == "tls"):
            alpn =  inboundSetting["tlsSettings"]["certificates"]["alpn"]
        serviceName = inboundSetting["grpcSettings"]["serviceName"]
        grpcSecurity = inboundSetting["security"]
    elif netType == "tcp":
        headerType = inboundSetting["tcpSettings"]["header"]["type"]
        if headerType != "none":
            
          path = inboundSetting["tcpSettings"]["header"]["request"]["path"][0]
          try:
              
             host = inboundSetting["tcpSettings"]["header"]["request"]["headers"]["host"][0]
          except:
             host = inboundSetting["tcpSettings"]["header"]["request"]["headers"]["Host"][0]
                 
    elif netType == "ws":
       
       
        path = inboundSetting["wsSettings"]["path"]
        try:
            host = inboundSetting["wsSettings"]["headers"]["host"]
        except:
            host=""    
    elif netType == "kcp":
        kcpType = inboundSetting["kcpSettings"]["header"]["type"]
        kcpSeed = inboundSetting["kcpSettings"]["seed"]

    if protocol == "trojan":
        conf = ""
        if tls != "none":
            conf += "&security=tls&flow=xtls-rprx-direct"
        if netType == "tcp" :
            if  headerType == "http":
              conf += "&headerType=http"
       
        if netType == "grpc":
            conf += f"&serviceName={serviceName}"
        newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}{conf}#{email}"
    elif protocol == "vless":
        conf = ""
        if netType == "tcp":
            if headerType == "http":
                conf += "&headerType=http"
            if tls == "xtls":
                conf += "&flow=xtls-rprx-direct"
            if host ==None :
                host=""    
            newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}&security={tls}&path=/&host={host}{conf}#{email}"
        elif netType == "ws":
            newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}&security={tls}&path=/&host={host}{conf}#{email}"
        elif netType == "kcp":
            newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}&security={tls}&headerType={kcpType}&seed={kcpSeed}#{email}"
        elif netType == "grpc":
            if tls == "tls":
                newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}&security={tls}&serviceName={serviceName}&sni={serviceName}#{email}"
            else:
                newConfig = f"{protocol}://{uuid}@{serverName}:{port}?type={netType}&security={tls}&serviceName={serviceName}#{email}"
    elif protocol == "vmess":
        vmessConf = {
            "v": "2",
            "ps": f"{email}",
            "add": serverName,
            "port": int(port),
            "id": uuid,
            "aid": 0,
            "net": netType,
            "type": "none",
            "tls": "none",
            "path": "",
            "host":  ""

        }
        # 'add': 'Irancell1.mobserver4.site', 'aid': '0', 'alpn': '', 'fp': '', 'host': 'telewebion.com', 'id': '448dd3b4-a12c-4add-9411-c6f7199df302', 'net': 'tcp', 'path': '/', 'port': '443', 'ps': 'ALIREZA200', 'scy': 'auto', 'sni': '', 'tls': 'none', 'type': 'http', 'v': '2'
   
        if headerType != None:
            vmessConf["type"] = headerType
        elif kcpType != None:
            vmessConf["type"] = kcpType
        else:
            vmessConf["type"] = "none"

        if host != None or host != "none":
            vmessConf["host"] = host
        if path == None or path == '':
            vmessConf["path"] = "/"
        else:
            vmessConf["path"] = path
        if  tls == "" or tls =="none":
            vmessConf["tls"] = "none"

        else:
            vmessConf["tls"] = tls
        if headerType == "http":
            vmessConf["path"] = "/"
            vmessConf["type"] = headerType
        if netType == "kcp":
            if kcpSeed != None or kcpSeed != "":
                vmessConf["path"] = kcpSeed

        if netType == "grpc":
            vmessConf['type'] = grpcSecurity
            vmessConf['scy'] = 'auto'
        res = json.dumps(vmessConf)
        res =res[1:]

        res = "{\n"  +  res.replace("}","\n}")
        res = res.replace("," ,",\n ")
        sample_string_bytes = res.encode("ascii")
    
        base64_bytes = base64.b64encode(sample_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        
        newConfig = f"vmess://{base64_string}"
    return newConfig




@app.on_callback_query()
async def joined(client: app, call: CallbackQuery):
 if CheckBlock(call.from_user.id)==False:
    if  call.data == "AddServer":
        if readfils()["admin"] == call.from_user.id or CheckAdmin(call.from_user.id)[0] == True:
           url = None
           name = None
           user = None
           password = None
           allow = False
           
           answer = await call.message.chat.ask(" آدرس سرور خود را وارد کنید مثل حالت زیر : \n  https://example.com:1234 \n https://example.com:1234/test \n http://192.168.0.1:1234 \n http://192.168.0.1:1234/test")
           if answer.text =='انصراف': return await GetMain(call)
           url = answer.text
           answer = await call.message.chat.ask("دامنه سرور را بدون port و http وارد کنید: ")
           if answer.text =='انصراف': return await GetMain(call)
           name = answer.text
           answer = await call.message.chat.ask("نام کاربری سرور را وارد کنید:")
           if answer.text =='انصراف': return await GetMain(call)
           user = answer.text
           answer = await call.message.chat.ask("پسورد سرور را وارد کنید:")
           if answer.text =='انصراف': return await GetMain(call)
           password = answer.text
           await call.message.reply("⌛️",reply_markup=ReplyKeyboardMarkup([['sanaei','alireza'],['انصراف']],resize_keyboard=True))
           answer = await call.message.chat.ask("لطفا نوع سرور را انتخاب کنید: (alireza,sanaei)")
           if answer.text =='انصراف': return await GetMain(call)
           ServerType =  answer.text 
           if ServerType != 'sanaei' and ServerType != 'alireza':
               await call.message.reply('🙏🏼 لطفا از دکمه های مشخص شده استفاده کنید')
               await GetMain(call)
               return
               

           if user == None or url == None or password == None or name == None:
             allow = False
           else:

               try:
                async with httpx.AsyncClient() as clienthttp :
                  response =  await clienthttp.post(url=f"{url}/login",data={"username":f"{user}","password":f"{password}"})
                  if response.status_code == 200:
                     current_session = response.headers.get(
                    "Set-Cookie").split("; ")[0]
                     allow = AddServerToConf(
                    user, name, password, url, current_session,ServerType)
              
                     if allow == True:
                    
                      await call.message.reply("سرور با موفقیت اضافه شد ✅\n"   ,)
        # reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(
        #               " v1.1.3 علیرضا", callback_data=f"ChangeTypeAlireza_{allow[1]}"), InlineKeyboardButton(
        #              "ساده ", callback_data=f"ChangeTypeSimple_{allow[1]}")]])
                     else:
                        await call.message.reply("❌هنگام ذخیره اطلاعات به مشکل خوردیم")
                  else:
                    await call.message.reply("❌نتونستم به سرور وارد بشم")

               except:
                  await call.message.reply(" ❌هنگام وارد شدن به سرور مشکلی پیش امده لطفا مقادیر را به درستی وارد کنید")
                  return

    if "ARSChangeUserName_" in call.data:
        if CheckAdmin(call.from_user.id)[0] == True:

         srId = int(call.data.split("_")[1])
         if srId == None:
            await call.message.reply("لطفا مقادیر را به درستی وارد کنید!")

         else:
           if CheckServer(srId) ==True:
            answer = await call.message.chat.ask('🔺 | لطفا نام کاربری جدید را وارد کنید ')
            try:
               

                 context.execute(f"UPDATE Servers SET UserName = '{answer.text}'  where serverId = {srId}")
                 db.commit()
                 await call.message.reply("✅ | اطلاعات با موفقیت تغییر کرد ",reply_markup=back_btn)            
              

            except:
                await call.message.reply("هنگام تغییر مشکلی پیش امد")
                
           else:
                await call.message.reply("سرور پیدا نشد")
               
                    
    if "ARSChangeName_" in call.data:
     if CheckAdmin(call.from_user.id)[0] == True:

        srId = int(call.data.split("_")[1])
        if srId == None:
            await call.message.reply("لطفا مقادیر را به درستی وارد کنید!")

        else:
         if CheckServer(srId) ==True: 
            answer = await call.message.chat.ask('🔺 | لطفا نام جدید را وارد کنید ')
            try:
              
                
                 context.execute(f"UPDATE Servers SET Name = '{answer.text}'  where serverId = {srId}")
                 db.commit()
                 await call.message.reply("✅ | اطلاعات با موفقیت تغییر کرد ",reply_markup=back_btn)            

            except:
                await call.message.reply("هنگام تغییر مشکلی پیش امد")
         else:
                await call.message.reply("سرور پیدا نشد")
    if "ARSChangeURl_"in call.data:
     if CheckAdmin(call.from_user.id)[0] == True:

        srId = int(call.data.split("_")[1])
        if srId == None:
            await call.message.reply("لطفا مقادیر را به درستی وارد کنید!")

        else:
           if CheckServer(srId) ==True:  
            answer = await call.message.chat.ask('🔺 | لطفا ادرس جدید را وارد کنید ')
            try:
                server = []
                
                context.execute(f"UPDATE Servers SET URl = '{answer.text}'  where serverId = {srId}")
                db.commit()
                await call.message.reply("✅ | اطلاعات با موفقیت تغییر کرد ",reply_markup=back_btn)                              
                

            except:
                await call.message.reply("هنگام تغییر مشکلی پیش امد")
           else:
                await call.message.reply("سرور پیدا نشد")
    if "ARSChangePass_" in call.data:
     if CheckAdmin(call.from_user.id)[0] == True:

        srId = int(call.data.split("_")[1])
        if srId == None:
            await call.message.reply("لطفا مقادیر را به درستی وارد کنید!")

        else:
         if CheckServer(srId) ==True: 
            answer = await call.message.chat.ask('🔺 | لطفا پسورد جدید را وارد کنید ')
            try:
                 context.execute(f"UPDATE Servers SET Pass = '{answer.text}'  where serverId = {srId}")
                 db.commit()
                 await call.message.reply("✅ | اطلاعات با موفقیت تغییر کرد ",reply_markup=back_btn)            

            except:
                await call.message.reply("هنگام تغییر مشکلی پیش امد")
         else:
                await call.message.reply("سرور پیدا نشد")      
    if "ARSChangeCookie_" in call.data:
     if CheckAdmin(call.from_user.id)[0] == True:
        await call.answer("این بخش دیگه به کار نمیاد",True)
    if "ShowData_" in call.data:
       if CheckAdmin(call.from_user.id)[0] == True:
            server = []
            srId = int(call.data.split("_")[1])
            if srId != None:
                  context.execute(f"SELECT * FROM Servers WHERE serverId={srId};")
                  server= context.fetchone()
                  
                  if server != None:
                        mes = f"  \n 📡 {server[2]}\n\n🌐 {server[1]}\n \n🙎‍♂️ {server[3]}\n\n🔑 {server[4]}\n  ▪️▫️▪️▫️▪️▫️▪️ "
                        btnserver =InlineKeyboardMarkup([[InlineKeyboardButton("ویرایش نام",callback_data=f"ARSChangeName_{server[0]}"),InlineKeyboardButton("ویرایش ادرس",callback_data=f"ARSChangeURl_{server[0]}")],
                        [InlineKeyboardButton("ویرایش نام کاربری",callback_data=f"ARSChangeUserName_{server[0]}"),InlineKeyboardButton("ویرایش پسورد",callback_data=f"ARSChangePass_{server[0]}")],
                        
                        [InlineKeyboardButton(f"حذف", callback_data=f"ARSDeleteServer_{server[0]}"),InlineKeyboardButton("افزودن کانفیگ",callback_data=f"AddConfig_{server[0]}")],[InlineKeyboardButton("اپدیت کوکی",callback_data=f"ARSChangeCookie_{server[0]}")],[InlineKeyboardButton("بازگشت 🔙", callback_data="ServersList")]])
                        await call.edit_message_text(mes, reply_markup=btnserver)
                  else:
                      await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ", reply_markup=back_btn)
    if "ARSDeleteServer_" in call.data: 
     if CheckAdmin(call.from_user.id)[0] == True:
      

        srId = int(call.data.split("_")[1])
        if srId == None:
            await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ", reply_markup=back_btn)
        else:
            try:
                 context.execute(f"DELETE FROM Servers where serverId = {srId}")
                 db.commit()
               
                 await call.edit_message_text("با موفقیت حذف شد | ⚠",reply_markup=back_btn)
                     

            except:
                await call.edit_message_text("هنگام تغییر مشکلی پیش امد")
    if "ARSShowConf_"in call.data:
     srId = int(call.data.split("_")[1])
     if srId == None:
             await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ")
     else:
    #   try:   
        context.execute(f"SELECT * FROM UserConfig WHERE configId={srId};")
        confD= context.fetchone()
        context.execute(f"SELECT * FROM Servers WHERE serverId={confD[6]};")
        server= context.fetchone()
        uuid=       confD[1]
        email = ""
        enable = ""
        up = None
        addToDate=""
        down = None
        expiryTime = None
        total = None
        allow = False
        startUse =""
        trojan = False
        jalili_date = None
        consumption = None
        remaining = None
      
          
        origin= server[1].split("/")
        headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate',
  'X-Requested-With': 'XMLHttpRequest',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': f'{origin[0]}://{origin[2]}',
  'Connection': 'keep-alive',
  'Referer': f'{server[1]}/panel/inbounds',
  'Cookie': ''
}

        async with httpx.AsyncClient() as clienthttp:
          try:

             response =  await clienthttp.post(url=f"{server[1]}/login",data={"username":f"{server[3]}","password":f"{server[4]}"})
          
             session = response.headers.get("Set-Cookie").split("; ")[0]   
             headers['Cookie']  = f"lang=en-US; {session}"
             response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
          except:
           response = await  clienthttp.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
      
       
          info_json = json.loads(response.text)
          inbounds = info_json["obj"]
       
          for inbound in inbounds:
            if email != "":
                break
            settings = json.loads(inbound['settings'])
            for client in settings['clients']:
                if inbound["protocol"] == "trojan":
                    if trojan == True:
                        if uuid == client['password']:
                            email = client['email']
                            break

                else:
                    if uuid == client['id']:
                        email = client['email']
                        break

            if email != "":
               
                states = inbound['clientStats']
                for state in states:
                    if state["email"] == email:

                        total = str(
                            round(state['total'] / (1024 * 1024 * 1024), 2))+" GB"
                        up = round(state['up'] / (1024 * 1024 * 1024), 2)
                        down = round(state['down'] / (1024 * 1024 * 1024), 2)
                        if total == "0.0 GB":
                            total = "نامحدود"
                            remaining = "نامحدود"
                        else:
                            remaining = round(round(state['total'] / (1024 * 1024 * 1024), 2) - (up + down),2)

                       
                        consumption = str(round(down + up,2)) + "GB"
                        if state["enable"] == True:
                            enable = "فعال 🟢"

                        elif state["enable"] == False:
                            enable = "غیرفعال 🔴"

                        if state["expiryTime"] != 0:
                            if 0 > state["expiryTime"]:
                                if down + up == 0.0:
                                    startUse = "-شروع نشده-" 
                                mili = str(state["expiryTime"])[1:]
                                if int( round((int(mili)/86400000), 2)) < 1:
                                     addToDate +=  "کمتر از یک رو از اشتراک شما باقی مانده"
                                else:
                                    addToDate += "روز های باقی مانده"
                                    
                                mili = str(state["expiryTime"])[1:]
                                if int( round((int(mili)/86400000), 2)) < 1:
                                   jalili_date = ""
                               # else:
                                     #jalili_date = int(
                                    #round((int(mili)/86400000), 2))
                            else:
                                expiryTime = datetime.datetime.fromtimestamp(
                                    state["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
                                jalili_date = jdatetime.datetime.fromgregorian(day=expiryTime.day, month=expiryTime.month, year=expiryTime.year, hour=expiryTime.hour, minute=expiryTime.minute, second=expiryTime.second)
            
                               
                        elif state["expiryTime"] == 0:
                            jalili_date = "نامحدود"
   
                        allow = True
                      
                        try:
                              newConf = GetConfig(inbound["streamSettings"], uuid, email, inbound["port"],
                                           inbound["protocol"], server[2],str(inbound["remark"]))
                              mes =f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse} {str(jalili_date)} \n🌐 سرور: {server[2]}\n\n\n\n🔗 کانفیگ شما:\n <code>{newConf}</code>"
                              await call.edit_message_text(f"{mes}",reply_markup=ikb(array_chunk([("❌ حذف اکانت از لیست",f"DeleteUserConf_{srId}")],1)))
                              
                              if readfils()["admin"] == call.from_user.id or  CheckAdmin(call.from_user.id)[0] == True: 
                                 await call.message.reply_text("جهت استعلام مجدد،ابتدا روی (/start) کلیک کنید و از منوی زیر،گزینه اکانت های من را انتخاب کنید🔻",reply_markup=btn_Reply_admin)
                              else:
                                  await call.message.reply_text("جهت استعلام مجدد،ابتدا روی (/start) کلیک کنید و از منوی زیر،گزینه اکانت های من را انتخاب کنید🔻",reply_markup=btn_Reply)
                              break
                          
                              
                        except:
                            mes =f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse} {str(jalili_date)} \n🌐 سرور: {server[2]}\n هنگام ساخت کانفیگ شما مشکلی پیش اومده لطفا دوباره تست کنید"
                            await call.edit_message_text(f"{mes}",reply_markup=ikb(array_chunk([("❌ حذف اکانت از لیست",f"DeleteUserConf_{srId}")],1)))
                            if readfils()["admin"] == call.from_user.id or  CheckAdmin(call.from_user.id)[0] == True:  
                              await call.message.reply_text("جهت استعلام مجدد،ابتدا روی (/start) کلیک کنید و از منوی زیر،گزینه اکانت های من را انتخاب کنید🔻",reply_markup=btn_Reply_admin)
                            else:
                                  await call.message.reply_text("جهت استعلام مجدد،ابتدا روی (/start) کلیک کنید و از منوی زیر،گزینه اکانت های من را انتخاب کنید🔻",reply_markup=btn_Reply)
                            break      
                            
                     
                          
                          
    #   except:
    #             await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا  ادمین را اطلاع بدهید | ❌ ")
    if "DeleteUserConf_"in call.data:
      srId = int(call.data.split("_")[1])
      if srId == None:
             await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ")
      else:   
            try:
                 context.execute(f"DELETE FROM UserConfig where configId = {srId}")
                 db.commit()
               
                 await call.edit_message_text("با موفقیت حذف شد | ✅")
                     

            except:
                await call.edit_message_text("هنگام تغییر مشکلی پیش امد")
    if "AddConfig_" in call.data:
     if CheckAdmin(call.from_user.id)[0] == True:

        srId = int(call.data.split("_")[1])
        if srId == None:
            await call.message.reply("لطفا مقادیر را به درستی وارد کنید!")

        else:
         if CheckServer(srId) ==True:    
                  context.execute(f"SELECT * FROM Servers WHERE serverId={srId};")
                  server= context.fetchone()
                  numberOfConf = 0
                  anwser = await pyromod.Chat.ask(text="🔻 تعداد اکانت را وارد کنید:" , self=call.message.chat)
                  try:
                   numberOfConf =int(anwser.text)
                  except:
                     await call.message.reply("لطفا فقط عدد وارد کنید") 
                     return
                  anwser = await pyromod.Chat.ask(text="🔻 آیدی اینباند را وارد کنید:" , self=call.message.chat)
                  numberOfInbound = 0
                  try:
                   numberOfInbound =int(anwser.text)
                  except:
                     await call.message.reply("لطفا فقط عدد وارد کنید") 
                    
                     return
                  anwser = await pyromod.Chat.ask(text="🔻 حجم را به گیگ وارد کنید:(نامحدود=0)" , self=call.message.chat)
                
                  
                  volume =  float(anwser.text) * 1024 * 1024 *1024
                  anwser = await pyromod.Chat.ask(text="🔻 ماه را وارد کنید:(نامحدود=0)" , self=call.message.chat)
                  days = 0
                  if anwser.text != '0':
                      
                   days = int(anwser.text) * 31
                   monthCount = datetime.datetime.now() + datetime.timedelta(days=days)
                   endTimeMikro =str(int(datetime.datetime.timestamp(monthCount) ))+'000'
                  else:
                      endTimeMikro = 0
                  anwser = await pyromod.Chat.ask(text="🔻 پیشوند اکانت ها را وارد کنید:" , self=call.message.chat)
                  configName = anwser.text
                  anwser = await pyromod.Chat.ask(text="🔻 شماره شروع را وارد کنید:" , self=call.message.chat)
                  nmuberStart = 0
                  try:
                    nmuberStart = int(anwser.text)    
                  except:
                     await call.message.reply("لطفا فقط عدد وارد کنید") 
                     return
                        
                  i =1    
                  clients = ""
                  uuid = []
                  resFinal = []
                  mili = days
                  counter =  int( round((int(mili)*86400000), 2)) 
                  while i <= numberOfConf:
                    uuid=uuid4()
                    email = configName + f'{nmuberStart}'
                    nmuberStart += 1

                    resFinal.append([str(uuid),email])
                    if numberOfConf == i :
                     
                     clients+=('{"id": "'+ str(uuid) + '", "alterId": 0, "email": "'+email+'", "totalGB": '+str(int(volume))+' , "expiryTime": -'+str(counter)+', "enable": true, "tgId": "", "subId": ""}')
                    else:
                     clients+=('{"id": "'+ str(uuid) + '", "alterId": 0, "email": "'+email+'", "totalGB": '+str(int(volume))+', "expiryTime": -'+str(counter)+', "enable": true, "tgId": "", "subId": ""},')
                    i+=1      
                        

                  
           
                  data={"settings":'{"clients": [' + clients+ ']}',
                        
                        "id":f"{numberOfInbound}"
                        }
               
                  response = ""
                  origin= server[1].split("/")
                  headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.5',
  'Accept-Encoding': 'gzip, deflate',
  'X-Requested-With': 'XMLHttpRequest',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': f'{origin[0]}://{origin[2]}',
  'Connection': 'keep-alive',
  'Referer': f'{server[1]}/panel/inbounds',
  'Cookie': ''
} 
                  responsedata = ''
                  async with httpx.AsyncClient() as clienthhtp:
                     
                     response =  await clienthhtp.post(url=f"{server[1]}/login",data={"username":f"{server[3]}","password":f"{server[4]}"})
          
                     session = response.headers.get("Set-Cookie").split("; ")[0]   
                     headers['Cookie']  = f"lang=en-US; {session}"
                     response = await clienthhtp.post(server[1]+f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/addClient",headers=headers,data=data)  
        
                     responsedata= json.loads(response.text)   
                  if responsedata['success'] == True:
                           text = "\n"
                           response = None
                           async with httpx.AsyncClient() as client:
                          
                            try:
                                      response = await  client.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
                            except:
                                response = await  client.post(server[1] + f"/{'panel'if server[6]=='sanaei' else 'xui' }/inbound/list",headers= headers, timeout=6)
                       
                           info_json = json.loads(response.text)
                           inbounds = info_json["obj"]
                          
                           for inbound in inbounds:
                              if inbound['id']== numberOfInbound:
                                    counter = 0
                                    for  uuids in resFinal :
                                       
                                      text +="<code>" + GetConfig(inbound["streamSettings"], uuids[0], uuids[1], inbound["port"],
                                           inbound["protocol"], server[2],str(inbound["remark"])) + "</code>\n\n"
                                      counter+=1
                                      if counter == 8 :
                                        await call.message.reply(text=text )  
                                        counter = 0
                                        text =""          
                                          
                                    break  
                           if text != "":    
                              await call.message.reply(text=text )            
                                   
       
   
          
    
    if "ServersList" == call.data:
     if CheckAdmin(call.from_user.id)[0] == True:
        
        btns=[]
        context.execute("SELECT * FROM Servers;")
        servers=context.fetchall()
        if servers != []:
          mes = "لیست سرور ها در خدمت شما \n شما میتونید با کلیک روی هر دکمه تنظیمات دل خواه رو روی ان انجام بدید \n موفق باشید "
            
          for server in servers:
             btns.append((str(server[2]), f"ShowData_{str(server[0])}"))
       
          mes += f" \n \n 🔰 جمع سرور ها  {len(servers)} \n \n   ◾️◽️◾️◽️◾️◽️◾️◽️◾️  "
          btns.append(("بازگشت","manage"))
          lines = array_chunk(btns, 1)
          keyboard = ikb(lines)
          await call.edit_message_text(mes, reply_markup=keyboard)
        else:
          await call.edit_message_text("کابر گرامی شما هنوز سروری اضافه نکردید ... \n \"لطفا از بخش افزودن سرور اقدام به اضافه کردن کنید \"\n▪️▫️▪️▫️▪️▫️▪️▫️▪️ " , reply_markup=ikb(array_chunk(([("بازگشت","manage")]), 1)))
              
      
    if "manage" == call.data:
      if CheckAdmin(call.from_user.id)[0] == True:
              await call.edit_message_text(f"🔰 | سلام  {call.from_user.first_name} \n\n به بخش مدیریت ربات خود خوش آمدید \n میتوانید از منوی زیر انتخاب کنید 👇🏻 \n\n▪️▫️▪️▫️▪️▫️▪️▫️▪️",reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton("لیست سرور ها",callback_data="ServersList"),InlineKeyboardButton("افزودن سرور",callback_data="AddServer")],[InlineKeyboardButton("مدیریت کاربران",callback_data="manageUser"),InlineKeyboardButton("آمار ربات",callback_data="Amar")],[InlineKeyboardButton("مدیریت ربات",callback_data="manageBot")]]))
          
    if call.data =="manageUser":
        if CheckAdmin(call.from_user.id)[0] == True:
          if   CheckAdmin(call.from_user.id)[1] == True:
              await call.edit_message_text("👤 | به بخش مدیریت کاربران خوش امدید\n  ◾️◽️◾️◽️◾️◽️◾️◽️◾️ ",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("پیام به کاربر",callback_data="userMessage"),InlineKeyboardButton("مسدود کردن",callback_data="blockUser")],[InlineKeyboardButton("آزاد کردن کاربر",callback_data="unblockUser"),InlineKeyboardButton("مدیریت ادمین ها",callback_data="ManageAdmin")],[InlineKeyboardButton("ارسال پیام همگانی",callback_data="SendMessageAllUser")],[InlineKeyboardButton("بازگشت",callback_data="manage")]]))
          elif CheckAdmin(call.from_user.id)[1] == False:
              await call.edit_message_text("👤 | به بخش مدیریت کاربران خوش امدید\n  ◾️◽️◾️◽️◾️◽️◾️◽️◾️ ",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("پیام به کاربر",callback_data="userMessage"),InlineKeyboardButton("مسدود کردن",callback_data="blockUser")],[InlineKeyboardButton("آزاد کردن کاربر",callback_data="unblockUser"),InlineKeyboardButton("ارسال پیام همگانی",callback_data="SendMessageAllUser")],[InlineKeyboardButton("بازگشت",callback_data="manage")]]))
               
    if call.data=="ManageAdmin":
      if CheckAdmin(call.from_user.id)[0] == True:
       if   CheckAdmin(call.from_user.id)[1] == True:         
        context.execute(f"SELECT * FROM Users where ISAdmin = 1;")
        Admins = context.fetchall()   
     
        btns=[]
        for admin in Admins:
          if CheckAdmin(admin[1])[1] == False:
              btns.append((f"{admin[1]}","ARSISGOD"))
              btns.append(("❌",f"removeAdmin_{admin[0]}"))
        btns.append(("افزودن ادمین","AddAdmin"))
        btns.append(("بازگشت","manageUser"))
        lines = array_chunk(btns,2)      
        await call.edit_message_text("ادمین های خود را مدیریت کنید",reply_markup=ikb(lines))
    if call.data =="AddAdmin":
        anwser =await call.message.chat.ask("لطفا ای دی عدد ادمین جدید را وارد کنید")
        context.execute(f"SELECT * FROM Users where uuid = {int(anwser.text)};")
        User = context.fetchone()    
        if User ==None:
           await call.message.reply("این کاربر هنوز داخل ربات ثبت نام نکرده است")
        else  :
         try:
            uuid = int(anwser.text)
            
            context.execute(f"UPDATE Users SET ISAdmin = 1  where uuid = {uuid}")
            db.commit()
            await call.message.reply("با موفقیت ادمین شد")
            
         except:    
            await call.message.reply("لطفا فقط عدد وارد کنید")
    if "removeAdmin_" in call.data:
        srId = int(call.data.split("_")[1])
        if srId == None:
            await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ", reply_markup=back_btn)
        else:
            try:
                  context.execute(f"UPDATE Users SET ISAdmin = 0  where userId = {srId}")
                  db.commit()
               
                  await call.edit_message_text("با موفقیت حذف شد | ⚠",reply_markup=ikb(array_chunk([("بازگشت","ManageAdmin")],1)))
                     

            except:
                await call.edit_message_text("هنگام تغییر مشکلی پیش امد")
    if call.data =="unblockUser":
        anwser =await call.message.chat.ask("🔺 |  ای دی عدد کاربری که قصد رفع محدودیتش را دارید ارسال کنید")
        
        context.execute(f"SELECT * FROM Users where uuid = {int(anwser.text)};")
        User = context.fetchone()    
        if User ==None:
           await call.message.reply("این کاربر هنوز داخل ربات ثبت نام نکرده است")
        elif User[2]==0:
           await call.message.reply("این کاربر مسدود نیست ")
        else:   
            context.execute(f"UPDATE Users SET IsBlock = 0  where uuid = {int(anwser.text)}")
            db.commit()
            await call.message.reply("کاربر رفع مسدود شد ")
            await client.send_message(int(anwser.text),"کاربر گرامی شما از سمت مدیریت رفع مسدودیت شدید")
    if call.data == "blockUser":
       if CheckAdmin(call.from_user.id)[0] == True :
              
        anwser =await call.message.chat.ask("🔺 | لطفا id کاربری که قصد مسدود کردنش را دارید وارد کنید ") 
   
        context.execute(f"SELECT * FROM Users where uuid = {int(anwser.text)};")
        User = context.fetchone()    
        if User ==None:
           await call.message.reply("این کاربر هنوز داخل ربات ثبت نام نکرده است")
        elif   CheckAdmin(int(anwser.text))[1] == True:   
            
            await call.message.reply("این کاربر ادمین  اصلی میباشد ")
        
        elif User[2]==1:
           await call.message.reply("این کاربر از قبل مسدود میباشد ")
           
        else:   
           if CheckAdmin(call.from_user.id)[1] == True :
            
             context.execute(f"UPDATE Users SET IsBlock = 1  where uuid = {int(anwser.text)}")
             db.commit()
             await call.message.reply("کاربر مسدود شد ")
           elif CheckAdmin(call.from_user.id)[0] == True and CheckAdmin(int(anwser.text) ) == [True,False]:
             await call.message.reply("این کاربر مانند شما ادمین است")
           else    :
                
             context.execute(f"UPDATE Users SET IsBlock = 1  where uuid = {int(anwser.text)}")
             db.commit()
             await call.message.reply("کاربر مسدود شد ")
            
    if call.data =="SendMessageAllUser":
      if   CheckAdmin(call.from_user.id)[0] == True:         
       
        context.execute("SELECT * FROM PublicMessage WHERE IsSended = 0")
        res = context.fetchone()

        if res !=None:
            await call.message.reply("یک پیام در صف است کمی صبر کنید")
            return
        title = ""  
        meesageBody = ""
        anwser =await call.message.chat.ask(f"🔻 عنوان پیام را وارد کنید:") 
        title = anwser.text
        anwser =await call.message.chat.ask(f"🔻 متن پیام را وارد کنید:")
        meesageBody = anwser.text
        context.execute("INSERT INTO PublicMessage(Title , Description, AddUser) VALUES(?, ?, ?)",(title ,meesageBody,call.from_user.id))
        db.commit()
        await call.message.reply("پیام با موفقیت به لیست اضافه شد")

               
        
                
    if call.data == "userMessage":
       if   CheckAdmin(call.from_user.id)[0] == True:           
        anwser =await call.message.chat.ask(" 🔺 | لطفا ای دی عددی کاربر را ارسال کنید ")      
        context.execute(f"SELECT * FROM Users where uuid = {int(anwser.text)};")
        User = context.fetchone()    
        if User ==None:
           await call.message.reply("این کاربر هنوز داخل ربات ثبت نام نکرده است")
        else:
          anwser =await call.message.chat.ask(" 🔺 | لطفا متنی که میخواهید را ارسال کنید ")      
          await client.send_message(User[1],f"{anwser.text}")
          await call.message.reply_text("پیام برای کاربر مورد نظر ارسال شد ")
    if call.data =="Amar":
     if   CheckAdmin(call.from_user.id)[0] == True:           
       context.execute("SELECT * FROM Servers;")
       servers=context.fetchall()
       if  servers==None:
           serverLenth = 0
       else:
           serverLenth =len(servers) 
           
       context.execute("SELECT * FROM Users;")
       users = context.fetchall()
       if  users ==None:
           userLen = 0
       else:
           userLen =len(users)    
       context.execute("SELECT * FROM Users where IsBlock = 1;")
       UserBlock = context.fetchall()
       if  UserBlock ==None:
           BlockUserLen = 0
       else:
           BlockUserLen = len(UserBlock)  
       context.execute("SELECT * FROM Users where ISAdmin = 1;")
       Admin = context.fetchall()
      
       if  Admin ==None:
           adminLen = 0
       else:
           adminLen = len(Admin) 
       context.execute("SELECT * FROM UserConfig;")
       userConfig  = context.fetchall()
       if  userConfig ==None:
           ConfigLen = 0
       else:
           ConfigLen = len(userConfig) 
       btnBackToMain = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت",callback_data="manage")]])
       await call.edit_message_text(f"🔴 به قسمت امار ربات خوش آمدید \n\nتعداد سرور : {serverLenth}\nتعداد یوزر : {userLen}\nتعداد ادمین : {adminLen}\nکاربران مسدود : {BlockUserLen}\nکانفیگ  ها : {ConfigLen}\n ◾️◽️◾️◽️◾️◽️◾️◽️◾️ ",reply_markup=btnBackToMain)
    if "manageBot" in call.data:
     if   CheckAdmin(call.from_user.id)[1] == True:         
        
        if "manageBotchangeState_" in call.data:
            
             srId = int(call.data.split("_")[1])
             if srId == None:
                await  call.edit_message_text("هنگام دریافت اطلاعات به مشکل خوردیم لطفا توسعه دهنده را اطلاع بدهید | ❌ ", reply_markup=back_btn)
             if srId==1:
                  context.execute(f"UPDATE ManageBot SET State = 0  where Id = 1")
                  db.commit()
                 
             elif srId==0:
                  context.execute(f"UPDATE ManageBot SET State = 1  where Id = 1")
                  db.commit()
       
                  
           
                 
                  
        data = []
        btns=[]
        context.execute("SELECT * FROM ManageBot;")
        data.append(context.fetchone())
       
        if data[0][1]==1:
            btns.append(("روشن",f"manageBotchangeState_{data[0][1]}"))
            btns.append(("وضعیت ربات","َARS"))
        elif data[0][1]==0:
            btns.append(("خاموش",f"manageBotchangeState_{data[0][1]}"))
            btns.append(("وضعیت ربات","َARS"))
        
        btns.append((f" {data[0][3]} روز مانده  ", "ChangeHours"))    
        btns.append(("زمان هشدار", "ARS"))    
        btns.append((f"{data[0][4]} GB ", "ChangeTotal"))
        btns.append(("حجم هشدار", "ARS"))    
        btns.append((f"{data[0][5]}  ", "backupChanel"))
        btns.append(("چنل بکاپ", "ARS"))    
        btns.append(("بازگشت" , "manage")) 
        
        await call.edit_message_text("🔰 |  به بخش مدیریت خوش آمدی",reply_markup=ikb(array_chunk(btns,2)))
    
            
    if call.data == "ChangeHours": 
      if   CheckAdmin(call.from_user.id)[1] == True:           
        anwers =  await call.message.chat.ask("🔺 | لطفا ساعت جدید را وارد نمایید")
        try:
            res=  int(anwers.text)
            context.execute(f"UPDATE ManageBot SET Time = {res}  where Id = 1")
            db.commit()
            await  call.message.reply("با موفقیت تغییر کرد")
        except:
           anwers =  await call.message.chat.ask("🔺 | لطفا فقط عدد وارد کنید !  ")
           try:
               res = int(anwers.text)
               context.execute(f"UPDATE ManageBot SET Time = {res}  where Id = 1")
               db.commit()
               await call.message.reply("با موفقیت تغییر کرد")
           except:
             await call.message.reply("مقادیر مشکل داشت دوباره و به درستی امتحان کنید !")
        
        
    if call.data == "ChangeTotal":
       if   CheckAdmin(call.from_user.id)[1] == True:          
         anwers = await call.message.chat.ask("🔺 | لطفا حجم جدید را وارد کنید")      
         try:
            res=  int(anwers.text)
            context.execute(f"UPDATE ManageBot SET Total = {res}  where Id = 1")
            db.commit()
            await  call.message.reply("با موفقیت تغییر کرد")
         except:
           anwers =  await call.message.chat.ask("🔺 | لطفا فقط عدد وارد کنید !  ")
           try:
               res = int(anwers.text)
               context.execute(f"UPDATE ManageBot SET Total = {res}  where Id = 1")
               db.commit()
               await call.message.reply("با موفقیت تغییر کرد")
           except:
             await call.message.reply("مقادیر مشکل داشت دوباره و به درستی امتحان کنید !")    
    if call.data == "backupChanel":
       if   CheckAdmin(call.from_user.id)[1] == True:          
         anwers = await call.message.chat.ask("🔺 | لطفا کانال جدید را وارد کنید")      
         context.execute(f"UPDATE ManageBot SET Chanel = '{anwers.text}'  where Id = 1")
         db.commit()
         await  call.message.reply("با موفقیت تغییر کرد")
         
                      
        # context.execute(f"UPDATE Servers SET Total = {anwers.text}  where Id = 1")
        # db.commit()
 else:
     
                await call.message.reply("کاربر گرامی شما مسدود شده اید لطفا از طریق پشتیبانی پیگیری کنید")
                return     
     
     
scheduler.start()     
app.run()
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
        # if "ChangeTypeAlireza_" in call.data:
    #      if readfils()["admin"] == call.from_user.id:
    #         servers = []
    #         finish = None
    #         counter = 0
    #         srId = int(call.data.split("_")[1])
    #         if srId != None:
                
    #             with open("db/servers.json") as fp:
    #                 servers = json.load(fp)
    #             for server in servers:
    #                 if server["id"] == srId:
    #                     servers[counter]["type"] = 1  
    #                     file = open("db/servers.json", 'w')
    #                     file.write(json.dumps(servers))
    #                     file.close()
    #                     finish =True
    #                     await call.edit_message_text("علیرضا با موفقیت انتخاب وتغییر ایجاد شد")
                        
    #                 counter += 1    
                
    #             if finish!=None:
    #              await call.edit_inline_reply_markup("😑در کمال تعجب سرور پیدا نشد لطفا توسعه دهنده بدبخت را خبر کنید")       
    #         else:
    #                await call.edit_message_text(" هنگام دریافت اطلاعات مشکلی پیش آمده ")         
    # if "ChangeTypeSimple_" in call.data:
    #      if readfils()["admin"] == call.from_user.id:
    #         servers = []
    #         finish = None
    #         counter = 0
    #         srId = int(call.data.split("_")[1])
    #         if srId != None:
                
    #             with open("db/servers.json") as fp:
    #                 servers = json.load(fp)
    #             for server in servers:
    #                 if server["id"] == srId:
    #                     servers[counter]["type"] = 0
    #                     file = open("db/servers.json", 'w')
    #                     file.write(json.dumps(servers))
    #                     file.close()
    #                     finish =True
    #                     await call.edit_message_text("نوع ساده با موفقیت انتخاب وتغییر ایجاد شد")
                        
    #                 counter += 1    
                
    #             if finish!=None:
    #              await call.reply("😑در کمال تعجب سرور پیدا نشد لطفا توسعه دهنده بدبخت را خبر کنید")       
    #         else:
    #                await call.edit_message_text(" هنگام دریافت اطلاعات مشکلی پیش آمده ")             
    #    show data

            # info = InlineKeyboardMarkup([[InlineKeyboardButton(
            #     email, callback_data="solarteam"), InlineKeyboardButton(
            #     "ایمیل ", callback_data="solarteam")], [InlineKeyboardButton(
            #         f"{up}  GB", callback_data="solarteam"), InlineKeyboardButton(
            #         "اپلود ", callback_data="solarteam")],
            #     [InlineKeyboardButton(
            #         f"{down}  GB", callback_data="solarteam"), InlineKeyboardButton(
            #         "دانلود ", callback_data="solarteam")],
            #     [InlineKeyboardButton(
            #         enable, callback_data="solarteam"), InlineKeyboardButton(
            #         "وضعیت ", callback_data="solarteam")],
            #     [InlineKeyboardButton(
            #         expiryTime, callback_data="solarteam"), InlineKeyboardButton(
            #         "تاریخ ", callback_data="solarteam")],
            #     [InlineKeyboardButton(
            #         f"{total}  GB", callback_data="solarteam"), InlineKeyboardButton(
            #         "کل", callback_data="solarteam")]],

            # )
# if call.data == "ShowServers":

    #     if readfils()["admin"] == call.from_user.id:
    #         servers = []

    #         btns = []
    #         with open("db/servers.json") as fp:
    #             servers = json.load(fp)
    #         mes = "لیست سرور ها در خدمت شما \n شما میتونید با کلیک روی هر دکمه تنظیمات دل خواه رو روی ان انجام بدید \n موفق باشید "
    #         try:
    #              for server in servers:
    #                btns.append((server["name"], f"ShowData_{server['id']}"))
    #            #   mes += f"  \n 〰〰〰〰〰〰〰〰〰〰〰〰〰〰〰 \n \n     : سرور با ادرس نام{server['name']}  \n \n : سرور با  ادرس{server['url']}  \n \n : سرور با نام کاربری{server['username']} \n \n : سرور با پسورد{server['pass']} \n \n ویرایش  نام سرور: /ARSChangeName_{server['id']}     \n \n ویرایش ادرس سرور : /ARSChangeURl_{server['id']} \n \n   ویرایش  نام کاربری: /ARSChangeUserName_{server['id']} \n \n   ویرایش کلمه عبور: /ARSChangePass_{server['id']}  \n \n   ویرایش  کوکی: /ARSChangeCookie_{server['id']}  \n \n   حذف  : /ARSDelete_{server['id']} "
    #              mes += f" \n \n جمع تمام سرور ها {len(servers)} \n \n     "
    #              lines = array_chunk(btns, 1)
    #              keyboard = ikb(lines)
    #         except:
    #             keyboard = ikb(("سروری موجود نیست", f"ars"))
                
    #         await call.edit_message_text(mes, reply_markup=keyboa










# d
#     email = ""
#     enable = ""
#     up = None
#     addToDate=""
#     down = None
#     expiryTime = None
#     total = None
#     allow = False
#     startUse =""
#     trojan = False
#     jalili_date = None
#     consumption = None
#     remaining = None
#     try:
#             response = requests.post(url + "/xui/inbound/list", headers={
#             "cookie": f"{str}"}, timeout=6).text
#     except:
#             response = requests.post(url + "/xui/inbound/list", headers={
#             "cookie": f"{session}"}, timeout=6).text    
       
#     info_json = json.loads(response)
#     inbounds = info_json["obj"]
       
#     for inbound in inbounds:
#             if email != "":
#                 break
#             settings = json.loads(inbound['settings'])
#             for client in settings['clients']:
#                 if inbound["protocol"] == "trojan":
#                     if trojan == True:
#                         if uuid == client['password']:
#                             email = client['email']
#                             break

#                 else:
#                     if uuid == client['id']:
#                         email = client['email']
#                         break

#             if email != "":
#                 print("test")
#                 states = inbound['clientStats']
#                 for state in states:
#                     if state["email"] == email:

#                         total = str(
#                             round(state['total'] / (1024 * 1024 * 1024), 2))+" GB"
#                         up = round(state['up'] / (1024 * 1024 * 1024), 2)
#                         down = round(state['down'] / (1024 * 1024 * 1024), 2)
#                         if total == "0.0 GB":
#                             total = "نامحدود"
#                             remaining = "نامحدود"
#                         else:
#                             remaining = round(round(state['total'] / (1024 * 1024 * 1024), 2) - (up + down),2)

                       
#                         consumption = str(round(down + up,2)) + "GB"
#                         if state["enable"] == True:
#                             enable = "فعال 🟢"

#                         elif state["enable"] == False:
#                             enable = "غیرفعال 🔴"

#                         if state["expiryTime"] != 0:
#                             if 0 > state["expiryTime"]:
#                                 if down + up == 0.0:
#                                     startUse = "-شروع نشده-" 
#                                 mili = str(state["expiryTime"])[1:]
#                                 if int( round((int(mili)/86400000), 2)) < 1:
#                                      addToDate +=  "کمتر از یک رو از اشتراک شما باقی مانده"
#                                 else:
#                                     addToDate += "روز های باقی مانده"
                                    
#                                 mili = str(state["expiryTime"])[1:]
#                                 if int( round((int(mili)/86400000), 2)) < 1:
#                                    jalili_date = ""
#                                # else:
#                                      #jalili_date = int(
#                                     #round((int(mili)/86400000), 2))
#                             else:
#                                 expiryTime = datetime.datetime.fromtimestamp(
#                                     state["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
#                                 jalili_date = jdatetime.datetime.fromgregorian(day=expiryTime.day, month=expiryTime.month, year=expiryTime.year, hour=expiryTime.hour, minute=expiryTime.minute, second=expiryTime.second)
            
                               
#                         elif state["expiryTime"] == 0:
#                             jalili_date = "نامحدود"
   
#                         allow = True
                      
                            
#                         return f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse} {str(jalili_date)} \n🌐 سرور: {server['name']}\n\n ▪️▫️▪️▫️▪️▫️▪️▫️▪️"
                     
                          
                          
              # @app.on_message(filters.regex("📋 استعلام اکانت") & ~ filters.command("start"))
# async def check_ID(client: app, m: Message):
#     servers = []

#     with open("db/servers.json") as fp:
#         servers = json.load(fp)

#     answer = await m.chat.ask('کانفیگ را از اکانت خود کپی کنید و ارسال کنید:')
#     uuid = 0
#     email = ""
#     enable = ""
#     up = None
#     addToDate=""
#     down = None
#     expiryTime = None
#     total = None
#     allow = False
#     startUse =""
#     trojan = False
#     jalili_date = None
#     consumption = None
#     remaining = None
#     if answer.text.strip().startswith("vless://"):
#         await answer.request.reply("کانفیگ شما دریافت شد و نتیجه تا دقایقی دیگر ارسال خواهد شد .\n \n  لطفا کمی صبر کنید... 🕒")
#         uuid = convert_link_vless(answer.text)
#     elif answer.text.strip().startswith("vmess://"):
        
#         uuid = convert_link_vmess(answer.text)
#         if(uuid=="configKosSher"):
#             await answer.request.reply("⚠ کانفیگ را به صورت کامل وارد کنید")
#             return
#         else:
#           print(uuid)
#           await answer.request.reply("کانفیگ شما دریافت شد و نتیجه تا دقایقی دیگر ارسال خواهد شد .\n \n  لطفا کمی صبر کنید... 🕒")
        
#     elif answer.text.strip().startswith("trojan://"):
#         await answer.request.reply("کانفیگ شما دریافت شد و نتیجه تا دقایقی دیگر ارسال خواهد شد .\n \n  لطفا کمی صبر کنید... 🕒")
#         uuid = FindTrojanPass(answer.text)
#         trojan = True
#     elif "vnext" in answer.text:
#         await answer.request.reply("کانفیگ شما دریافت شد و نتیجه تا دقایقی دیگر ارسال خواهد شد .\n \n  لطفا کمی صبر کنید... 🕒")
#         details = json.loads(answer.text)
        
#         if details["outbounds"][0]["protocol"] == "trojan":
#             trojan = True
#         uuid = details["outbounds"][0]["settings"]["vnext"][0]["users"][0]["id"]
#     elif answer.text.strip().startswith("wings://"):
#         await answer.request.reply("کانفیگ شما دریافت شد و نتیجه تا دقایقی دیگر ارسال خواهد شد .\n \n  لطفا کمی صبر کنید... 🕒")
#         data = wings(answer.text)
       
#         if data["outbound"]["protocol"] == "trojan":
#             trojan = True
#             uuid = data["outbound"]["uuid"]

        
#     else:
#         if  readfils()["admin"] == m.from_user.id:   
#             await answer.request.reply("⚠ کانفیگ ارسال شده صحیح نیست.\n \n توجه داشته باشید که کانفیگ را به صورت کامل باید ارسال کنید.در صورت نیاز،از منوی زیر گزینه راهنما را انتخاب کنید.",re)
   
#     for server in servers:
    
#         if email != "":
#             break

#         try:
#             response = requests.post(server["url"] + "/xui/inbound/list", headers={
#             "cookie": f"{server['session']}"}, timeout=6).text
#         except:
#             response = requests.post(server["url"] + "/xui/inbound/list", headers={
#             "cookie": f"{server['session']}"}, timeout=6).text    
       
#         info_json = json.loads(response)
#         inbounds = info_json["obj"]
       
#         for inbound in inbounds:
#             if email != "":
#                 break
#             settings = json.loads(inbound['settings'])
#             for client in settings['clients']:
#                 if inbound["protocol"] == "trojan":
#                     if trojan == True:
#                         if uuid == client['password']:
#                             email = client['email']
#                             break

#                 else:
#                     if uuid == client['id']:
#                         email = client['email']
#                         break

#             if email != "":
#                 states = inbound['clientStats']
#                 for state in states:
#                     if state["email"] == email:

#                         total = str(
#                             round(state['total'] / (1024 * 1024 * 1024), 2))+" GB"
#                         up = round(state['up'] / (1024 * 1024 * 1024), 2)
#                         down = round(state['down'] / (1024 * 1024 * 1024), 2)
#                         if total == "0.0 GB":
#                             total = "نامحدود"
#                             remaining = "نامحدود"
#                         else:
#                             remaining = round(round(state['total'] / (1024 * 1024 * 1024), 2) - (up + down),2)

                       
#                         consumption = str(round(down + up,2)) + "GB"
#                         if state["enable"] == True:
#                             enable = "فعال 🟢"

#                         elif state["enable"] == False:
#                             enable = "غیرفعال 🔴"

#                         if state["expiryTime"] != 0:
#                             if 0 > state["expiryTime"]:
#                                 if down + up == 0.0:
#                                     startUse = "-شروع نشده-" 
#                                 mili = str(state["expiryTime"])[1:]
#                                 if int( round((int(mili)/86400000), 2)) < 1:
#                                      addToDate +=  "کمتر از یک رو از اشتراک شما باقی مانده"
#                                 else:
#                                     addToDate += "روز های باقی مانده"
                                    
#                                 mili = str(state["expiryTime"])[1:]
#                                 if int( round((int(mili)/86400000), 2)) < 1:
#                                    jalili_date = ""
#                                # else:
#                                      #jalili_date = int(
#                                     #round((int(mili)/86400000), 2))
#                             else:
#                                 expiryTime = datetime.datetime.fromtimestamp(
#                                     state["expiryTime"] / 1000.0, tz=datetime.timezone.utc)
#                                 jalili_date = jdatetime.datetime.fromgregorian(day=expiryTime.day, month=expiryTime.month, year=expiryTime.year, hour=expiryTime.hour, minute=expiryTime.minute, second=expiryTime.second)
            
                               
#                         elif state["expiryTime"] == 0:
#                             jalili_date = "نامحدود"
   
#                         allow = True
#                         try:
#                               newConf = GetConfig(inbound["streamSettings"], uuid, email, inbound["port"],
#                                            inbound["protocol"], server["name"],str(inbound["remark"]))
#                               await m.reply_text(f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse} {str(jalili_date)} \n🌐 سرور: {server['name']}\n\n\n\n🔗 کانفیگ شما:\n <code>{newConf}</code>",reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(
#                       "📲 آموزش وارد کردن کانفیگ", url=f"https://akhbarnew.blogsky.com/1401/07/13/post-4/amozesh")]]))
#                               if readfils()["admin"] == m.from_user.id:  
#                                  await m.reply_text("جهت استعلام مجدد،از منوی زیر استعلام اکانت را انتخاب کنید🔻",reply_markup=btn_Reply_admin)
#                               else:
#                                   await m.reply_text("جهت استعلام مجدد،از منوی زیر استعلام اکانت را انتخاب کنید🔻",reply_markup=btn_Reply)
#                               break
                          
                              
#                         except:
#                             await m.reply_text(f"🔸 نام کاربری: {email}\n🔸 وضعیت: {enable}\n🔸 حجم کل: {total}\n🔸 حجم مصرفی: {consumption}\n🔸 حجم باقیمانده: {remaining}GB\n📆 انقضا: {startUse} {str(jalili_date)} \n🌐 سرور: {server['name']}\n\n\n\n🔗 کانفیگ شما:\n هنگام ساخت کانفیگ مشکلی پیش امده لطفا دوباره امتحان کنید❌",reply_markup= InlineKeyboardMarkup([[InlineKeyboardButton(
#                       "📲 آموزش وارد کردن کانفیگ", url=f"https://akhbarnew.blogsky.com/1401/07/13/post-4/amozesh")]]))
#                             if readfils()["admin"] == m.from_user.id:  
#                               await m.reply_text("جهت استعلام مجدد،از منوی زیر استعلام اکانت را انتخاب کنید🔻",reply_markup=btn_Reply_admin)
#                             else:
#                                   await m.reply_text("جهت استعلام مجدد،از منوی زیر استعلام اکانت را انتخاب کنید🔻",reply_markup=btn_Reply)
#                             break      
                        
   
          
#     if email=="" and allow!=True:
#         if readfils()["admin"] == m.from_user.id:    
#           await m.reply("❌ اکانت شما یافت نشد. \n \n نکته1:دقت کنید که کانفیگ را به صورت کامل وارد کنید. \n \n نکته2:در صورتی که از تاریخ انقضای اشتراک شما بیش از 3 روز گذشته باشد،اشتراک شما حذف و امکان استعلام وجود ندارد. \n \n نکته 3:کانفیگ را فقط از نرم افزار کپی کنید. \n\n نکته4:در صورتی که موارد بالا را رعایت کردید،مجدد امتحان کنید.",reply_markup=btn_Reply_admin)
#         else:
#           await m.reply("❌ اکانت شما یافت نشد. \n \n نکته1:دقت کنید که کانفیگ را به صورت کامل وارد کنید. \n \n نکته2:در صورتی که از تاریخ انقضای اشتراک شما بیش از 3 روز گذشته باشد،اشتراک شما حذف و امکان استعلام وجود ندارد. \n \n نکته 3:کانفیگ را فقط از نرم افزار کپی کنید. \n\n نکته4:در صورتی که موارد بالا را رعایت کردید،مجدد امتحان کنید.",reply_markup=btn_Reply)
              


    
        
  
