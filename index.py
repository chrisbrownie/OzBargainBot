from datetime import datetime, timedelta
import boto3
import json
import logging
import os
import sys
import time
import urllib
import urllib2

url = "https://www.ozbargain.com.au/api/live?last=%timestamp%&disable=comments%2Cvotes%2Cwiki&types=Ad%2CComp%2CForum"
linkbase = "https://www.ozbargain.com.au"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')


def generateUrl(url, timestamp):
    return url.replace("%timestamp%", str(timestamp))


def getDeals(url):
    webdata = urllib2.urlopen(url).read()
    items = json.loads(webdata)
    return items


def sendWebHook(url, deal, webhook_channel):
    print deal["title"]
    print url
    payload = {
        "channel": webhook_channel,
        "username": "OzBargain",
        "icon_url": "https://i2.wp.com/files.ozbargain.com.au/g/38.jpg?ssl=1",
        "attachments": [
            {
                    "text": deal["title"],
                    "fallback": deal["title"],
                    "callback_id": "deal",
                    "color": "#7F3F00",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "text": "Go To Deal",
                            "type": "button",
                            "url": linkbase + deal["link"],
                            "style": "primary"
                        },
                        {
                            "name": "deal",
                            "text": "More info",
                            "type": "button",
                            "value": "maze"
                        }
                    ]
            }
        ]
    }
    print json.dumps(payload)
    try:
        req = urllib2.Request(
            url, json.dumps(payload), {'Content-Type': 'application/json'}
        )
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
    except urllib2.HTTPError as e:
        print "Error!\n" + e.read()


def getLastRequestTimeStamp(bucketName, keyName='ozbb.txt'):
    # Grabs the last request timestamp from a file in an S3 bucket
    object = s3.Object(bucketName, keyName).get()
    body = object['Body'].read()
    return body


def putLastRequestTimeStamp(bucketName, timeStamp, keyName='ozbb.txt'):
    # Writes the last request timestamp to a file in an S3 bucket
    print timeStamp


def handler(event, context):
    webhook_url = os.environ['WEBHOOK_URL']
    webhook_channel = os.environ['WEBHOOK_CHANNEL']
    s3_bucket = os.environ['OZBB_S3_BUCKET']

    lastrequest = getLastRequestTimeStamp(bucketName=s3_bucket)

    print lastrequest
    exit()

    if lastrequest < 0:
        logger.info("Last request time not found, using 2 hours ago.")
        lastrequest = str(int(time.mktime(
            (datetime.now() - timedelta(hours=2)).timetuple())))

    parsedurl = generateUrl(url, lastrequest)
    dealdata = getDeals(parsedurl)
    newtimestamp = dealdata["timestamp"]
    deals = dealdata["records"]
    for deal in deals:
        sendWebHook(webhook_url, deal, webhook_channel)
    putLastRequestTimeStamp(s3_bucket, newtimestamp)
