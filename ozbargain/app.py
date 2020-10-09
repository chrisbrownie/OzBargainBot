from datetime import datetime, timedelta
import boto3
import json
import os
import re
import time
import urllib3

urlTemplate = "https://www.ozbargain.com.au/api/live?last=%timestamp%&disable=comments%2Cvotes%2Cwiki&types=Ad%2CComp%2CForum"
linkBase = "https://www.ozbargain.com.au"
default_timedelta_minutes = 30

http = urllib3.PoolManager()
ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])

def getLastRequestTimeStamp():
  try:
    lastRequestTimeStamp = GetSetting('state')
  except:
    lastRequestTimeStamp = str(int(time.mktime((datetime.now() - timedelta(minutes=default_timedelta_minutes)).timetuple())))
  return lastRequestTimeStamp

def generateUrl(url, timestamp):
  return url.replace("%timestamp%",str(timestamp))

def getDeals(url):
  r = http.request('GET', url)
  return json.loads(r.data)

def putLastRequestTimeStamp(timestamp):
  return 0

def sendMessage(deal,chat_id,bot_token):
  print(deal["title"])
  url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
  data = {
    'chat_id': chat_id,
    'text': "{}{}".format(linkBase,deal['link']),
  }
  r = http.request(
    'POST',
    url,
    fields=data
    )
  return r.data
  
def getSSMParameterValue(parameterPath):
  parameter = ssm.get_parameter(
    Name=parameterPath, 
    WithDecryption=True)
  result = parameter['Parameter']['Value']
  return result

def setSSMParameterValue(parameterPath,value):
  parameter = ssm.put_parameter(
    Name=parameterPath,
    Value=str(value),
    Type='SecureString',
    KeyId='alias/aws/ssm',
    Overwrite=True)
  return parameter

def GetSetting(settingName):
  envVar = settingName.upper()
  paramPath = f'{envVar}_PARAMETER'
  if envVar in os.environ:
    return os.environ[envVar]
  elif paramPath in os.environ:
    return getSSMParameterValue(os.environ[paramPath])
  else:
    raise Exception(f"You must specify either {envVar} or {paramPath}")

def lambda_handler(event, context):
  chat_id = GetSetting('chat_id')
  bot_token = GetSetting('bot_token')

  lastRequestTimeStamp = getLastRequestTimeStamp()

  url = generateUrl(urlTemplate, lastRequestTimeStamp)
  dealsData = getDeals(url)
  newTimestamp = dealsData["timestamp"]
  setSSMParameterValue(
    parameterPath=os.environ['STATE_PARAMETER'],
    value=newTimestamp)

  deals = dealsData["records"]
  for deal in deals:
    print(sendMessage(deal,chat_id,bot_token))

  return {
    "statusCode": 200,
    "body": json.dumps({"timestamp": newTimestamp})
  }

if __name__ == "__main__":
  lambda_handler(None,None)