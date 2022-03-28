# 访问openapi
# -*- coding: utf-8 -*-
import requests
import json
import logging
import datetime
logger = logging.getLogger(__name__)

KEY = 'SZ5W0DjDFSNlmcX3y'  # API key(私钥)
UID = ""  # 用户ID, TODO: 当前并没有使用这个值,签名验证方式将使用到这个值

LOCATION = 'beijing'  # 所查询的位置，可以使用城市拼音、v3 ID、经纬度等
API = 'https://api.seniverse.com/v3/weather/daily.json?'  # API URL，可替换为其他 URL
UNIT = 'c'  # 单位
LANGUAGE = 'zh-Hans'  # 查询结果的返回语言

headers = {}
headers['Content-Type'] = 'application/json'
headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'


def fetch_weather(location, start=0, days=15):
    logger.info('location {}'.format(location))
    # try:
    result = requests.get(API, params={
        'key': KEY,
        'location': location,
        'language': LANGUAGE,
        'unit': UNIT,
        'start': start,
        'days': days
    }, headers=headers)
    logger.info('result {}'.format(result))
    return result.json()


def get_weather_by_day(location, day):
    result = fetch_weather(location, start=day)
    normal_result = {
        "location": result["results"][0]["location"],
        "result": result["results"][0]['daily']
    }

    return normal_result


def get_weather_by_date(location, date):
    day_timedelta = date - datetime.datetime.today().date()
    one_day_timedelta = datetime.timedelta(days=1)
    day = day_timedelta // one_day_timedelta
    result = fetch_weather(location, start=day)
    normal_result = {
        "location": result["results"][0]["location"],
        "result": result["results"][0]['daily'][day]
    }

    return normal_result


if __name__ == '__main__':
    # default_location = "广州"
    # result = fetch_weather(default_location, 2)
    # print(json.dumps(result, ensure_ascii=False))

    default_location = "合肥"
    result = get_weather_by_day(default_location, 2)
    print(json.dumps(result, ensure_ascii=False))
