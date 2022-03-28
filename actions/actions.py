from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, AllSlotsReset, Restarted
from datetime import datetime, timedelta
from service.common import text_to_date, get_text_weather_date, text_date_to_number_date
from service.chatapi import get_response
from rasa_sdk.types import DomainDict


def text_date_to_int(text_date):
    if text_date == "今天":
        return 0
    if text_date == "明天":
        return 1
    if text_date == "昨天":
        return -1

    # in other case
    return None


weekday_mapping = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]


def weekday_to_text(weekday):
    return weekday_mapping[weekday]


class ActionQueryTime(Action):
    def name(self) -> Text:
        return "action_query_time"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        current_time = datetime.now().strftime("%H:%M:%S")
        dispatcher.utter_message(text=current_time, image="https://i.imgur.com/nGF1K8f.jpg")

        return []


class ActionQueryDate(Action):
    def name(self) -> Text:
        return "action_query_date"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        text_date = tracker.get_slot("date_time") or "今天"

        int_date = text_date_to_int(text_date)
        if int_date is not None:
            delta = timedelta(days=int_date)
            current_date = datetime.now()

            target_date = current_date + delta

            dispatcher.utter_message(text=target_date.strftime("%Y-%m-%d"))
        else:
            dispatcher.utter_message(text="系统暂不支持'{}'的日期查询".format(text_date))

        return [AllSlotsReset()]


class ActionQueryWeekday(Action):
    def name(self) -> Text:
        return "action_query_weekday"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        text_date = tracker.get_slot("date_time") or "今天"

        int_date = text_date_to_int(text_date)
        if int_date is not None:
            delta = timedelta(days=int_date)
            current_date = datetime.now()

            target_date = current_date + delta

            dispatcher.utter_message(text=weekday_to_text(target_date.weekday()))
        else:
            dispatcher.utter_message(text="系统暂不支持'{}'的星期查询".format(text_date))

        return [AllSlotsReset()]


class ActionWeather(Action):
    def name(self) -> Text:
        return "action_weather_form_submit"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        date_text = tracker.get_slot("date_time")
        address = tracker.get_slot("address")
        date_number = text_date_to_number_date(date_text)
        if isinstance(date_number, str):
            msg = "暂不支持查询 {} 的天气".format(date_text)
            dispatcher.utter_message(msg)
        else:
            dispatcher.utter_message(templete="utter_working_on_it")
            try:
                weather_info = get_text_weather_date(address, date_text, date_number)
            except Exception as e:
                exec_msg = str(e)
                dispatcher.utter_message(exec_msg)
            else:
                dispatcher.utter_message(weather_info)
        return [Restarted()]


class ActionChat(Action):
    def name(self) -> Text:
        return "action_default"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # 访问图灵机器人API(闲聊)
        text = tracker.latest_message.get('text')
        message = get_response(text)
        if message is not None:
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_template('utter_default', tracker, silent_fail=True)
        return [UserUtteranceReverted()]


class ValidateWeatherForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_weather_form"

    @staticmethod
    def date_time_db() -> List[Text]:
        """Database of supported cuisines"""
        return ["今天", "明天", "后天"]

    def validate_date_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate datetime value."""

        if slot_value.lower() in self.date_time_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"date_time": slot_value}
        else:
            # validation failed, set this slot to None so that the
            # user will be asked for the slot again
            return {"date_time": None}

    @staticmethod
    def address_db() -> List[Text]:
        """Database of supported cuisines"""
        return ["上海", "北京", "赣州", "天津", "重庆"]

    def validate_address(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate datetime value."""

        if slot_value.lower() in self.address_db():
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"address": slot_value}
        else:
            # validation failed, set this slot to None so that the
            # user will be asked for the slot again
            return {"address": None}
