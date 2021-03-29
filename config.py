import sqlite3
import random
import difflib
import uuid
from threading import Thread
import time
import json
import datetime

"""
permission:
  0. 示例权限 仅返回示例内容
  1. 仅允许randget/get1st         每日调用次数300次
  2. 允许randget/get1st/getword   每日调用次数500次
  3. 允许POST upload              每日调用次数800次
  4. 允许POST delete              不限调用次数
"""

errors = [
  {
    "status": "ERROR",
    "error_id": 50000,
    "error_info": "missing some data in url"
  },
  {
    "status": "ERROR",
    "error_id": 50001,
    "error_info": "sign verify failed"
  },
  {
    "status": "ERROR",
    "error_id": 50002,
    "error_info": "value error"
  },
  {
    "status": "ERROR",
    "error_id": 50003,
    "error_info": "overly similar strings"
  },
  {"title": u"Curewords API - \u5fc3\u7075\u9e21\u6c64","interfaces": [{"method": "get","path": "/api","value": "?value=getword/get1st/randget&appid=youappid&secret=youkey","response": [{"info": "String","status": "String","words": ["string"]}]}]},
  {
    "status": "ERROR",
    "error_id": 50005,
    "error_info": "data dont have key 'word'"
  },
  {
    "status": "ERROR",
    "error_id": 50006,
    "error_info": "id does not exist(in data)"
  },
  {
    "status": "ERROR",
    "error_id": 50007,
    "error_info": "id does not exist(in database)"
  },
  {
    "status": "ERROR",
    "error_id": 50008,
    "error_info": "delete failed"
  },
  {
    "status": "ERROR",
    "error_id": 50009,
    "error_info": "unknown error"
  },
  {
    "status": "ERROR",
    "error_id": 50010,
    "error_info": "Permission Denied"
  },
  {
    "status": "ERROR",
    "error_id": 50011,
    "error_info": "api usage has reached the upper limit"
  }
]

connect = sqlite3.connect("AppData.db", check_same_thread=False)
cursor = connect.cursor()

# temp_words = []

def cursorParse(data):
  for num in range(len(data)):
    data[num] = data[num][0]
  return data

class APItoken():

  @staticmethod
  def getSecret(appid):
    cursor.execute(f"SELECT secret FROM token WHERE appid = '{str(appid)}'")
    return cursor.fetchall()[0][0]

  @staticmethod
  def getPermission(appid):
    cursor.execute(f"SELECT permission FROM token WHERE appid = '{str(appid)}'")
    return int(cursor.fetchall()[0][0])
  
  @staticmethod
  def getCount(appid):
    cursor.execute(f"SELECT usecount FROM token WHERE appid = '{str(appid)}'")
    return int(cursor.fetchall()[0][0])

  @staticmethod
  def addCount(appid):
    count = APItoken.getCount(appid) + 1
    print(f"[INFO] APPID[{str(appid)}] count + 1")
    cursor.execute(f"UPDATE token SET usecount={str(count)} WHERE appid = '{str(appid)}'")
    connect.commit()

class cureword():

  @staticmethod
  def getparse(value,appid):
    """
    GET请求
    """
    permission = APItoken.getPermission(appid)
    usecount = APItoken.getCount(appid)
    if permission >= 1:
      if permission == 1 and usecount >= 300:
        return errors[11]
      elif permission == 2 and usecount >= 500:
        return errors[11]
      elif permission == 3 and usecount >= 800:
        return errors[11]
      else:
        if value == "get1st":
          APItoken.addCount(appid)
          return {
            "status": "OK",
            "info": "get the latest word",
            "words": cureword.get1st()
          }
        elif value == "randget":
          APItoken.addCount(appid)
          return {
            "status": "OK",
            "info": "random get a word",
            "words": cureword.randget()
          }
        elif value == "getword":
          if permission >= 2:
            print(appid)
            APItoken.addCount(appid)
            return {
              "status": "OK",
              "info": "get all words",
              "words": cureword.getword()
            }
          else:
            return errors[10]
        else:
          return errors[2]
    elif permission == 0:
      #权限为0时的示例
      sample = ["这是一条例子","这是一条毒鸡汤(?)","这是一条鸡汤","这是示例中最新的句子"]
      if value == "get1st":
        return {
          "status": "OK",
          "info": "get the latest word",
          "words": sample[-1]
        }
      elif value == "randget":
        return {
          "status": "OK",
          "info": "random get a word",
          "words": sample[random.randint(0,3)]
        }
      elif value == "getword":
        return {
          "status": "OK",
          "info": "get all words",
          "words": sample
        }
      else:
        return errors[2] #value error

  @staticmethod
  def postparse(value,data,appid):
    """
    解析post请求
    """
    if permission >= 3:
      if permission == 3 and usecount >= 800:
        return errors[11]
      else:
        if value == "upload":
          APItoken.addCount(appid)
          return cureword.upload(data)
        else:
          return errors[2] #value error
    elif permission >= 4:
      if value == "delete":
        APItoken.addCount(appid)
        return cureword.delete(data)
      else:
        return errors[2] #value error
    else:
      if value == "upload" or value == "delete":
        return errors[10] #permission denied
      else:
        return errors[2] #value error


  @staticmethod
  def getword():
    """
    获取所有鸡汤 允许GET POST
    """
    cursor.execute("SELECT word FROM main")
    return cursorParse(cursor.fetchall())
  
  @staticmethod
  def get1st():
    """
    获取最新的一条鸡汤
    """
    words = cureword.getword()
    return words[-1].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
  
  @staticmethod
  def randget():
    """
    随机获取一条鸡汤
    """
    words = cureword.getword()
    return words[random.randint(0,len(words)-1)].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()

  @staticmethod
  def upload(data):
    """
    解析post收到的内容 与已有的内容判断
    """
    try:
      inw = data["word"]
    except:
      return errors[5]
    else:
      temp_words = cureword.getword()
      for num in range(len(temp_words)):
        if cureword.stringcompare(temp_words[num],inw):
          return errors[3]
      cursor.execute(f"INSERT INTO main (Word) VALUES ('{str(inw)}');")
      connect.commit()
      return {
        "status": "OK",
        "info": "uploaded to the database (admin will check it later)"
      }
  
  @staticmethod
  def stringcompare(str1,str2):
    return (difflib.SequenceMatcher(None, str1, str2).quick_ratio() >= 0.65)
  
  @staticmethod
  def delete(data):
    """
    解析post收到的内容 查看该id是否存在 返回数据 删除对应ID的鸡汤
    """
    try:
      iid = data["id"]
      iid = int(iid)
    except:
      return errors[6]
    else:
      cursor.execute("SELECT id FROM main")
      ids = cursorParse(cursor.fetchall())
      if iid in ids:
        cursor.execute(f"DELETE FROM main WHERE id = {str(iid)}")
        connect.commit()
        cursor.execute(f"SELECT id FROM main WHERE id = {str(iid)}")
        if len(cursor.fetchall()) == 0:
          return {
            "status": "OK",
            "info": f"Deleted data where id = {str(iid)}"
          }
        else:
          return errors[8]
      else:
        return errors[7]

Run = True

def resetcount():
  while Run:
    if datetime.datetime.now().hour == 5 and datetime.datetime.now().minute == 10:
      connect = sqlite3.connect("AppData.db", check_same_thead=False)
      cursor = connect.cursor()
      print("[INFO] usecount reset")
      cursor.execute("UPDATE token SET usecount=0")
      connect.commit()
      cursor.close()
    time.sleep(60)

t1 = Thread(target=resetcount)
t1.setDaemon(True)
t1.start()