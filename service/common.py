import datetime
from typing import Optional
from service.weatherapi import get_weather_by_day
import logging
logger = logging.getLogger(__name__)


def text_to_date(text_date: str) -> Optional[datetime.date]:
    """convert text based Chinese date info into datatime object

    if the convert is not supprted will return None
    """

    today = datetime.datetime.now()
    one_more_day = datetime.timedelta(days=1)

    if text_date == "今天":
        return today.date()
    if text_date == "明天":
        return (today + one_more_day).date()
    if text_date == "后天":
        return (today + one_more_day * 2).date()

    # Not supported by weather API provider freely
    if text_date == "大后天":
        # return 3
        return (today + one_more_day * 3).date()

    if text_date.startswith("星期"):
        # not supported yet
        return None

    if text_date.startswith("下星期"):
        # not supported yet
        return None

    # follow APIs are not supported by weather API provider freely
    if text_date == "昨天":
        return None
    if text_date == "前天":
        return None
    if text_date == "大前天":
        return None


def get_text_weather_date(address, date_time, date_time_number):
    try:
        result = get_weather_by_day(address, date_time_number)
        logger.info('**** get weather result : {} ****'.format(result))
    except Exception as e:
        text_message = str(e)
    else:
        text_message_tpl = """
            {} {} ({}) 的天气情况为：白天：{}；夜晚：{}；气温：{}-{} °C
        """
        text_message = text_message_tpl.format(
            result['location']['name'],
            date_time,
            result['result'][0]['date'],
            result['result'][0]['text_day'],
            result['result'][0]['text_night'],
            result['result'][0]['low'],
            result['result'][0]['high'],
        )

    return text_message


def text_date_to_number_date(text_date):
    if text_date == "今天":
        return 0
    if text_date == "明天":
        return 1
    if text_date == "后天":
        return 2

    # Not supported by weather API provider freely
    if text_date == "大后天":
        return 3
        # return text_date

    if text_date.startswith("星期"):
        # TODO: using calender to compute relative date
        return text_date

    if text_date.startswith("下星期"):
        # TODO: using calender to compute relative date
        return text_date

    # follow APIs are not supported by weather API provider freely
    if text_date == "昨天":
        return text_date
    if text_date == "前天":
        return text_date
    if text_date == "大前天":
        return text_date


if __name__ == '__main__':
    weatherinfo = get_text_weather_date("上海", "明天", 1)
    print(weatherinfo)