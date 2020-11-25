import json
import openpyxl
import re
import datetime
import sys
from os import path
import subprocess
import os
from typing import Dict, Optional, List
from member import MemberInfo, MemberInfoLibrary
from path_util import PathUtil
from agenda import Agenda, Session


def try_get_str(s):
    return str(s) if s is not None else ""


class Meeting:
    def __init__(self, month: int, day: int, is_english: bool, year=None):
        self._function_role_taker = {}  # type: Dict[str, MemberInfo]
        self._info = {}  # type: Dict[str, str]
        self._year = year if year is not None else datetime.datetime.now().year
        self._month = month
        self._day = day
        self._is_english = is_english
        self._theme = "TBD"
        self._speakers = []  # type: List[MemberInfo]
        self._new_member_count = -1

        with open(PathUtil().get_config_path("time_dict"), "r", encoding="utf-8") as time_dict_file:
            self._time_dict = json.load(time_dict_file)
            time_dict_file.close()

        with open(PathUtil().get_config_path("roles"), "r", encoding="utf-8") as roles_file:
            self._roles = json.load(roles_file)
            roles_file.close()

    @property
    def date_str(self) -> str:
        return "{2}{0:02}{1:02}".format(
            self._month,
            self._day,
            self._year
        )

    @property
    def is_english(self) -> bool:
        return self._is_english

    def set_info(self, key, value):
        self._info[key] = value

    @property
    def language(self):
        return "English" if self.is_english else "Chinese"

    def theme(self) -> str:
        return self._theme

    def __str__(self):
        info_dict = {
            "theme": self._theme,
            "date_str": self.date_str,
            "function roles": {},
            "speeches": []
        }
        for role, role_taker in self._function_role_taker.items():
            info_dict["function roles"][role] = role_taker.english_name
        for speaker in self._speakers:
            info_dict["speeches"].append({"speaker": speaker.english_name, "topic": speaker.last_speech_topic})

        return json.dumps(
            info_dict, indent=2
        )

    def try_get_info(self, key):
        if key in self._info:
            return self._info[key].strip()
        return ""

    def speech_count(self):
        return len(self._speakers)

    def parse_info(self, member_lib: MemberInfoLibrary):
        self._speakers.clear()
        try:
            self._new_member_count = int(self.try_get_info("NM"))
        except:
            self._new_member_count = -1

        self._theme = self.try_get_info("Theme")

        for i in range(1, 5):
            speaker_name = self.try_get_info("SP{}".format(i))
            speech_topic = self.try_get_info("SP{} Topic".format(i))
            if len(speaker_name) is not 0:
                role_taker = member_lib.assign_role(
                    speaker_name,
                    "Speaker".format(i),
                    self.date_str,
                    topic=speech_topic
                )

                self._speakers.append(role_taker)
            evaluator_name = self.try_get_info("IE{}".format(i))
            self._function_role_taker["IE{}".format(i)] = member_lib.assign_role(
                evaluator_name, "IE", self.date_str, topic=speech_topic)

        for role in self._roles:
            role_taker_name = self.try_get_info(role["name"])
            if len(role_taker_name) is 0 and "nick" in role:
                role_taker_name = self.try_get_info(role["nick"])
            if len(role_taker_name) is 0 and "default_taker" in role:
                role_taker_name = role["default_taker"]

            self._function_role_taker[role["name"]] = member_lib.assign_role(
                role_taker_name,
                role["name"],
                self.date_str,
                self._theme
            )

    def role_taken(self, role_name) -> bool:
        if role_name in self._function_role_taker:
            return self._function_role_taker[role_name].english_name != "TBD"
        return False

    @property
    def have_prepared_speech(self):
        return len(self._speakers) != 0

    def append_event(self, session, role_name, event, duration, show_duration=True):
        role_name_dict = {
            "SAA": "Sergeant at Arms (SAA)",
            "GE": "General Evaluator",
            "TTM": "Table Topic Master",
            "TTE": "Table Topic Evaluator"
        }
        session.append_event(
            duration=duration,
            role_name=role_name_dict[role_name] if role_name in role_name_dict else role_name,
            role_taker=self._function_role_taker[role_name],
            event=event,
            show_duration=show_duration
        )

    def opening_session(self, start_time):
        opening_session = Session(start_time)

        if self.role_taken("SAA"):
            self.append_event(
                opening_session,
                duration=20,
                role_name="SAA",
                event="Registration/Greeting",
                show_duration=False
            )
            self.append_event(
                opening_session,
                duration=4,
                role_name="Toastmaster",
                event="Meeting Opening"
            )
            self.append_event(
                opening_session,
                duration=5,
                role_name="SAA",
                event="Welcome Guests  (20s/P)"
            )
        else:
            self.append_event(
                opening_session,
                duration=20,
                role_name="VPM",
                event="Registration/Greeting",
                show_duration=False
            )
            self.append_event(
                opening_session,
                duration=4,
                role_name="Toastmaster",
                event="Meeting Opening"
            )
            self.append_event(
                opening_session,
                duration=5,
                role_name="VPM",
                event="Welcome Guests  (20s/P)"
            )

        self.append_event(
            opening_session,
            duration=1,
            role_name=self.real_ge,
            event="Evaluation Team: Purpose and Members"
        )

        self.append_event(
            opening_session,
            duration=1,
            role_name="Timer",
            event="Timer's Guidelines"
        )

        if self.role_taken("Ah Counter"):
            self.append_event(
                opening_session,
                duration=1,
                role_name="Ah Counter",
                event="Ah-Counter's Guidelines"
            )

        if self.role_taken("Word Smith"):
            self.append_event(
                opening_session,
                duration=2,
                role_name="Word Smith",
                event="Word Smith's Guidelines"
            )

        if self.role_taken("GE"):
            self.append_event(
                opening_session,
                duration=1,
                role_name="GE",
                event="Return control to Toastmaster"
            )
        self.append_event(
            opening_session,
            duration=1,
            role_name="Toastmaster",
            event="Introduce the Table Topic Master"
        )
        return opening_session

    def table_topic_session(self, start_time):
        table_topic_session = Session(start_time, title="Table Topic Session")
        if self.role_taken("TTE"):
            self.append_event(
                table_topic_session,
                duration=25,
                role_name="TTM",
                event="Theme Introduction & Table Topic Session"
            )
            self.append_event(
                table_topic_session,
                duration=6,
                role_name="TTE",
                event="Table Topic Evaluation"
            )
        else:
            self.append_event(
                table_topic_session,
                duration=30,
                role_name="TTM",
                event="Theme Introduction & Round Table"
            )

        self.append_event(
            table_topic_session,
            duration=8,
            role_name="Toastmaster",
            event="Break Time",
            show_duration=False
        )
        return table_topic_session

    def prepared_session(self, start_time):
        prepared_session = Session(start_time, title="Prepared Speech Session")
        for i, speaker in enumerate(self._speakers):
            o_s = ["1st", "2nd", "3rd", "4th"]
            self.append_event(
                prepared_session,
                duration=1,
                role_name="Toastmaster",
                event="Introduce the {} Speaker".format(o_s[i])
            )
            prepared_session.append_event(
                duration=7,
                role_name="Prepared Speaker {}".format(i + 1),
                event=speaker.last_speech_topic,
                role_taker=speaker
            )
        return prepared_session

    def evaluation_session(self, start_time):
        evaluation_session = Session(start_time, title="Evaluation Session")
        self.append_event(
            evaluation_session,
            duration=1,
            role_name=self.real_ge,
            event="Evaluation Session Opening"
        )
        for i, speaker in enumerate(self._speakers):
            o_s = ["1st", "2nd", "3rd", "4th"]
            evaluation_session.append_event(
                duration=3,
                role_name="Individual Evaluator {}".format(i + 1),
                event="Evaluate the {} Speaker".format(o_s[i]),
                role_taker=self._function_role_taker["IE{}".format(i+1)]
            )

        if self.role_taken("Ah Counter"):
            self.append_event(
                evaluation_session,
                duration=2,
                role_name="Ah Counter",
                event="Ah-Counter's Report"
            )

        if self.role_taken("Word Smith"):
            self.append_event(
                evaluation_session,
                duration=2,
                role_name="Word Smith",
                event="Word Smith's Report"
            )

        self.append_event(
            evaluation_session,
            duration=2,
            role_name="Timer",
            event="Timer's Report"
        )

        self.append_event(
            evaluation_session,
            duration=1,
            role_name="GE" if self.role_taken("GE") else "Toastmaster",
            event="Request Feedbacks from Audience"
        )

        if self.role_taken("GE"):
            self.append_event(
                evaluation_session,
                duration=5,
                role_name="GE",
                event="General Evaluator's Report"
            )

        if self._new_member_count > 0:
            self.append_event(
                evaluation_session,
                duration=5*self._new_member_count,
                role_name="VPM",
                event="Induction of New Members",
                show_duration=False
            )

        self.append_event(
            evaluation_session,
            duration=2,
            role_name="Toastmaster",
            event="Conclusion"
        )

        self.append_event(
            evaluation_session,
            duration=2,
            role_name="President",
            event="Meeting Closing"
        )

        return evaluation_session

    @property
    def real_ge(self) -> str:
        return "GE" if self.role_taken("GE") else "Toastmaster"

    def to_agenda(self, output_path):
        agenda = Agenda(self.language, self._theme, len(self._speakers))

        # opening
        agenda.append_session(self.opening_session(datetime.datetime(self._year, self._month, self._day, 18, 45)))

        # table topic session
        agenda.append_session(self.table_topic_session(agenda.current_datetime))

        # prepared session
        if self.have_prepared_speech:
            agenda.append_session(self.prepared_session(agenda.current_datetime))

        agenda.append_session(self.evaluation_session(agenda.current_datetime))
        agenda.dump(output_path)


class ToastmasterAgendaGenerator:
    def __init__(self, current_year=None):
        self.time_dict = {
        }
        self._current_year = current_year

    @property
    def path_util(self):
        return PathUtil()

    @classmethod
    def strip_name(cls, member_name: str):
        return re.sub(r"[\ud83c\ufe0f\udf3f\u5973\u795e\u7537\ud83d\udf38\udf3b]|(\[.*])|(N/A)", "", member_name).strip()

    @classmethod
    def read_info_from_call_role(cls, call_role_text, year=None):
        meetings = []
        meeting_info = None  # type: Optional[Meeting]
        for line in call_role_text.split('\n'):
            m = re.match(r"([0-9]+)/([0-9]+) *\((Chinese|English)\)", line.replace(u"中文", "Chinese"))
            if m is not None:
                if meeting_info is not None:
                    meetings.append(meeting_info)
                meeting_info = Meeting(
                    month=int(m.group(1)),
                    day=int(m.group(2)),
                    year=year,
                    is_english=True # (m.group(3) == "English")
                )
            elif line.find(":") is not -1:
                ti = line.find(":")
                meeting_info.set_info(line[:ti].strip(), cls.strip_name(line[ti+1:]))

        if meeting_info is not None:
            meetings.append(meeting_info)
        return meetings

    def generate_agenda(self, call_role_path=None, member_info_path=None, update_member_info=False):
        if call_role_path is None:
            call_role_path = self.path_util.default_meeting_info_path
        member_info_lib = MemberInfoLibrary(member_info_path)
        with open(call_role_path, "r", encoding="utf-8") as call_role_file:
            origin_text = call_role_file.read()
            call_role_file.close()

        year_str = path.split(call_role_path)[-1][:4]
        try:
            year = int(year_str)
        except:
            year = None

        for next_meeting in self.read_info_from_call_role(origin_text, year):
            # log
            with open(
                self.path_util.get_log_path("{0}.call_role.txt".format(next_meeting.date_str)),
                "w",
                encoding="utf-8"
            ) as meeting_log_file:
                meeting_log_file.write(origin_text)
                meeting_log_file.close()

            member_info_lib.clear_records(next_meeting.date_str)
            next_meeting.parse_info(member_info_lib)
            print(str(next_meeting))

            next_meeting.to_agenda(self.path_util.get_output_path("agenda.html"))

            if update_member_info is False:
                member_info_lib.dump(self.path_util.get_output_path(
                    "{0}.member_info.json".format(next_meeting.date_str)))

        if update_member_info is True:
            member_info_lib.dump()


def __main__():
    if len(sys.argv) == 3:
        _, current_log_path, call_role_path = sys.argv
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(call_role_path, current_log_path, update_member_info=True)
    elif len(sys.argv) == 1:
        for root, _, files in os.walk(PathUtil().get_log_path("")):
            files = sorted(filter(lambda x: x.endswith(".txt"), files))
            for file in files:
                generator = ToastmasterAgendaGenerator(file[:4])

                generator.generate_agenda(
                    call_role_path=path.join(root, file),
                    update_member_info=True
                )
    else:
        git_token = sys.argv[1]
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(update_member_info=True)

        status = subprocess.check_output(["git", "status"]).decode("utf-8")
        print(status)
        if status.find("data/member_info.json") is not -1:
            current_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call([
                "git",
                "commit",
                "-m",
                "feat: auto-generated change",
                "-m",
                "preview link: "
                "https://htmlpreview.github.io/?https://github.com/elliotzh/ms-toastmaster/blob/"
                "{}/agenda_generator/output/agenda.html".format(current_branch)
            ])
            run = subprocess.run([
                "git", "remote", "set-url", "origin",
                "https://{}@github.com/eliiotz/ms-toastmaster.git".format(git_token)
            ])
            run = subprocess.run(["git", "push"])
            print(run.stderr)
            print(run.stdout)


if __name__ == "__main__":
    # generator = ToastmasterAgendaGenerator()
    # generator.generate_agenda(update_member_info=True)
    __main__()
