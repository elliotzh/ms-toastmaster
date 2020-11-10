from path_util import PathUtil
import json
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from member import MemberInfo
from datetime import datetime, timedelta


class Session:
    def __init__(self, base_time: datetime, title=None):
        self._title = title
        self._rows = []
        self._base_time = base_time
        self._current_time = base_time

    def append_event(self, duration, role_name, event, role_taker: MemberInfo, show_duration=True):
        d = str(duration)
        if duration >= 20:
            g, y, r = "1", "1.5", "2"
        elif duration >= 5:
            g, y, r = str(duration - 2), str(duration - 1), str(duration)
            d = "{}-{}".format(g, r)
        elif duration >= 3:
            g, y, r = str(duration - 1), str(duration - 0.5), str(duration)
        else:
            g, y, r = "", "", str(duration)

        if show_duration is False:
            g, y, r = "", "", str(duration)
            d = str(duration)

        self._rows.append(Session.create_row([
            ("col-time", self._current_time.strftime("%I:%M %p")),
            ("col-role", role_name),
            ("col-event", event),
            ("col-role", role_taker.english_name),
            ("col-time", d),
            ("col-card", g),
            ("col-card", y),
            ("col-card", r),
        ]))

        self._current_time += timedelta(minutes=duration)

    def dump_to_element(self):
        soup = BeautifulSoup("<div class=\"session\"></div>", features="html.parser")
        if self._title is not None:
            soup.append(Session.create_row([("col-12 head", self._title)]))
        for row in self._rows:
            soup.append(row)
        return soup

    @classmethod
    def create_row(cls, columns):
        soup = BeautifulSoup(features="html.parser")
        head_row = soup.new_tag("div")
        head_row["class"] = "row"
        for i, column in enumerate(columns):
            _class, value = column
            head_column = soup.new_tag("div")
            head_column["class"] = "column {}".format(_class)
            head_column.string = value
            if i == len(columns) - 1:
                head_column["class"] = head_column["class"] + " last-column"
            head_row.append(head_column)
        return head_row

    @property
    def current_datetime(self):
        return self._current_time


class Agenda:
    @classmethod
    def template_localization(cls, template_path, language,
                              additional_dict: Optional[Dict[str, Dict[str, str]]] = None):
        with open(template_path, "r", encoding="utf-8") as html_file:
            html_template = html_file.read()
            html_file.close()
        with open(PathUtil().get_config_path("localization"), "r", encoding="utf-8") as localization_file:
            localization_dict = json.load(localization_file)  # type: Dict[str, Dict[str, str]]
            localization_file.close()

        if additional_dict is not None:
            localization_dict.update(additional_dict)

        for key, v_dict in localization_dict.items():
            value = v_dict["default"] if language not in v_dict else v_dict[language]
            html_template = html_template.replace("{{" + key + "}}", value)
        return html_template

    def __init__(self, language, theme, speech_count=3):
        self._template_str = Agenda.template_localization(
            PathUtil().get_template("default.html"),
            language,
            {
                "theme": {
                    "default": theme,
                },
                "speech_count": {
                    "default": str(speech_count),
                }
            }
        )
        self._sessions = []  # type: List[Session]

    def append_session(self, session: Session):
        self._sessions.append(session)
        return session

    def dump(self, output_path):
        current_soup = BeautifulSoup(self._template_str, features="html.parser")
        body = current_soup.find("div", id="body")
        for session in self._sessions:
            body.append(session.dump_to_element())
        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(current_soup.prettify())
            out_file.close()

    @property
    def current_datetime(self):
        return self._sessions[-1].current_datetime


def __main__():
    for language in ["English", "Chinese"]:
        agenda = Agenda(language, "test theme")
        session = Session(datetime(2020, 11, 5, 16, 40))
        session.append_event(
            duration=20,
            role_name="Sergeant at Arms (SAA)",
            role_taker=MemberInfo({
                "English Name": "Bonnie Wang",
                "Chinese Name": "Baoni",
                "Speech Records": [],
                "Role Records": [],
            }),
            event="Registration/Greeting",
            show_duration=False
        )
        session.append_event(
            duration=4,
            role_name="Toastmaster",
            role_taker=MemberInfo({
                "English Name": "Elliot Zhang",
                "Chinese Name": "Xingzhi",
                "Speech Records": [],
                "Role Records": [],
            }),
            event="Meeting Opening & Welcome Guests  (20s/P)"
        )

        session = Session(agenda.append_session(session).current_datetime, title="Table Topic Session")
        session.append_event(
            duration=25,
            role_name="Table Topic Master",
            role_taker=MemberInfo({
                "English Name": "Kay",
                "Chinese Name": "Li Kang",
                "Speech Records": [],
                "Role Records": [],
            }),
            event="Theme Introduction & Table Topic Session"
        )
        session.append_event(
            duration=6,
            role_name="Table Topic Evaluator",
            role_taker=MemberInfo({
                "English Name": "Raymond Lu",
                "Chinese Name": "Raymond",
                "Speech Records": [],
                "Role Records": [],
            }),
            event="Table Topic Evaluation"
        )
        session.append_event(
            duration=1,
            role_name="Toastmaster",
            role_taker=MemberInfo({
                "English Name": "Elliot Zhang",
                "Chinese Name": "Xingzhi",
                "Speech Records": [],
                "Role Records": [],
            }),
            event="Return control to Toastmaster"
        )
        agenda.append_session(session)

        agenda.dump(PathUtil().get_output_path("{}.html".format(language)))


if __name__ == "__main__":
    __main__()
