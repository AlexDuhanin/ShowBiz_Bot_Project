import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

calendar_id = "e16086764890938807f37f2df9396ce1d3d52d39aa65f909e69abf23728ed097@group.calendar.google.com"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly",
          "https://www.googleapis.com/auth/calendar"]


class Gcalendar:
    """Класс для взаимодействия с Google Calendar API."""


    def __init__(self, calendar_id=calendar_id):
        self.calendar_id = calendar_id

    def autorize(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        return creds

    def build(self):
        """Создаёт экземпляр сервиса Google Calendar API."""
        creds = self.autorize()
        service = build("calendar", "v3", credentials=creds)
        return service

    def events_list(self, count=10, name=None):
        """Получаем count число событий из календаря, у которых в названии есть name"""
        service = self.build()
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        events_result = (
            # Сортировку по name можно сделать и здесь.
            # https://developers.google.com/workspace/calendar/api/v3/reference/events/list#:~:text=q-,string,-%D0%9F%D0%BE%D0%B8%D1%81%D0%BA%20%D0%BF%D0%BE%20%D1%81%D0%B2%D0%BE%D0%B1%D0%BE%D0%B4%D0%BD%D0%BE%D0%BC%D1%83
            service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=count,
                singleEvents=True,
                orderBy="startTime",
                q=name  # на всякий случай еще здесь сортируем по name
            )
            .execute()
        )
        print('events', events_result)
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        if name:
            # Сортировка
            events = [event for event in events if name in event["summary"]]

        return events

        # print(events)
        # for event in events:
        #     start = event["start"].get("dateTime", event["start"].get("date"))
        # print(start, event["summary"])
        # print('id', event["id"])
        # test_event_id = event["id"]

    def event_get(self, event_id):
        """Получаем событие по его уникальному id"""
        service = self.build()
        body = (
            service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            )
            .execute()
        )
        if not body:
            return

        return body

    def event_update(self, event_id, summary=None, color_id=None,
                     start: datetime = None, end: datetime = None,
                     description=None):
        """Обновляем событие, изменяя ему необходимые данные
        Можно поменять: название (summary), дату (start/end), цвет (colorId)"""
        service = self.build()
        body = self.event_get(event_id=event_id)
        if not body: return None

        if summary: body["summary"] = summary
        if color_id: body["colorId"] = color_id
        if start: body["start"] = start
        if end: body["end"] = end
        if description: body["description"] = description

        result = (
            service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=body
            ).execute()
        )
        print('result', result)

# calendar = Gcalendar()

# events = calendar.events_list(count=1, name="ABC")
# print(events)
# event = events[0]
# calendar.event_update(event["id"], summary="QWERTY")