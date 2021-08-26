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
        self._skip_dict = set() # special hacks to skip events
        self._special_events = {} # hacks to get special events

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

        for i in range(1, 9):
            speaker_name = self.try_get_info("SP{}".format(i))
            speech_topic = self.try_get_info("SP{} Topic".format(i))
            if len(speaker_name) != 0:
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
            if len(role_taker_name) == 0 and "nick" in role:
                role_taker_name = self.try_get_info(role["nick"])
            if len(role_taker_name) == 0 and "default_taker" in role:
                role_taker_name = role["default_taker"]

            self._function_role_taker[role["name"]] = member_lib.assign_role(
                role_taker_name,
                role["name"],
                self.date_str,
                self._theme
            )

        # special events
        for se_type in ["SE_SP", "SE_TE"]:
            special_event = {}
            for attribute in ["role", "role taker", "topic", "duration", "gyr"]:
                special_event[attribute] = self.try_get_info("%s %s" % (se_type, attribute))
            if special_event["topic"]:
                self._special_events[se_type] = special_event

    def role_taken(self, role_name) -> bool:
        if role_name in self._function_role_taker:
            return self._function_role_taker[role_name].english_name != "TBD"
        return False

    @property
    def have_prepared_speech(self):
        return len(self._speakers) != 0

    @property
    def real_saa(self):
        return "SAA" if self.role_taken("SAA") else "VPM"

    def append_event(self, session, role_name, event, duration, role_taker=None, show_duration=True, gyr_cards=None):
        role_name_dict = {
            "SAA": "Sergeant at Arms (SAA)",
            "GE": "General Evaluator",
            "TTM": "Table Topic Master",
            "TTE": "Table Topic Evaluator"
        }
        if event.lower() in self._skip_dict:
            return
        if not role_taker:
            role_taker = self._function_role_taker[role_name]
        if role_taker == "[NONE]":
            return
        session.append_event(
            duration=duration,
            role_name=role_name_dict[role_name] if role_name in role_name_dict else role_name,
            role_taker=role_taker,
            event=event,
            show_duration=show_duration,
            gyr_cards=gyr_cards
        )

    def opening_session(self, start_time):
        opening_session = Session(start_time)

        self.append_event(
            opening_session,
            duration=20,
            role_name=self.real_saa,
            event="Registration/Greeting",
            show_duration=False
        )
        self.append_event(
            opening_session,
            duration=4,
            role_name="Toastmaster",
            event="Meeting Opening & Privacy Statement"
        )
        self.append_event(
            opening_session,
            duration=5,
            role_name=self.real_saa,
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
        return opening_session

    def table_topic_session(self, start_time):
        table_topic_session = Session(start_time, title="Table Topic Session")
        self.append_event(
            table_topic_session,
            duration=1,
            role_name="Toastmaster",
            event="Introduce the Table Topic Master"
        )
        if "SE_TE" in self._special_events.keys():
            self.append_special_event(table_topic_session, self._special_events["SE_TE"])
        if self.role_taken("TTE"):
            self.append_event(
                table_topic_session,
                duration=25,
                role_name="TTM",
                event="Theme Introduction & Table Topic Session",
                gyr_cards="1 1.5 2"
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
                event="Theme Introduction & Round Table",
                gyr_cards="1 1.5 2"
            )
        return table_topic_session

    def get_speech_duration(self, speaker: MemberInfo, speech_index=-1):
        duration = -1
        for time_setting in self._time_dict:
            if "levels" not in time_setting or speaker.current_level in time_setting["levels"]:
                duration = time_setting["duration"]

        overwrite = self.try_get_info("SPT{}".format(speech_index+1))
        if len(overwrite) != 0:
            duration = int(overwrite)

        return duration

    def append_special_event(self, session, special_event):
        role = special_event["role"]
        role_taker = special_event["role taker"]
        role_taker = MemberInfo({
            "English Name": role_taker,
            "Chinese Name": role_taker,
            "Role Records": [],
            "Speech Records": []})
        duration = int(special_event["duration"])
        topic = special_event["topic"]
        gyr = special_event["gyr"]
        show_duration = len(gyr) > 0
        self.append_event(
                session=session,
                role_name=role,
                duration=duration,
                event=topic,
                role_taker=role_taker,
                show_duration=show_duration,
                gyr_cards=gyr)


    def prepared_session(self, start_time):
        prepared_session = Session(start_time, title="Prepared Speech Session")
        if "SE_SP" in self._special_events.keys():
            self.append_special_event(prepared_session, self._special_events["SE_SP"])
        o_s = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
        for i, speaker in enumerate(self._speakers):
            self.append_event(
                prepared_session,
                duration=1,
                role_name="Toastmaster",
                event="Introduce the {} Speaker".format(o_s[i])
            )
            prepared_session.append_event(
                duration=self.get_speech_duration(speaker, speech_index=i),
                role_name="Prepared Speaker {}".format(i + 1),
                event=speaker.last_speech_topic,
                role_taker=speaker
            )

        for i, speaker in enumerate(self._speakers):
            prepared_session.append_event(
                duration=3,
                role_name="Individual Evaluator {}".format(i + 1),
                event="Evaluate the {} Speaker".format(o_s[i]),
                role_taker=self._function_role_taker["IE{}".format(i+1)]
            )

        if self.role_taken("GE"):
            self.append_event(
                prepared_session,
                duration=max(2, len(self._speakers)),
                role_name="GE",
                event="Evaluate Individual Evaluators"
            )

        #self.append_event(
        #    prepared_session,
        #    duration=5,
        #    role_name="Toastmaster",
        #    event="Break Time",
        #    show_duration=False
        #)
        return prepared_session

    def evaluation_session(self, start_time):
        evaluation_session = Session(start_time, title="Evaluation Session")
        self.append_event(
            evaluation_session,
            duration=1,
            role_name=self.real_ge,
            event="Evaluation Session Opening"
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
                duration=4,
                role_name="GE",
                event="General Evaluator's Report"
            )

        if self.role_taken("Guest Speaker"):
            self.append_event(
                evaluation_session,
                role_name="Guest Speaker",
                event=self.try_get_info("GS Topic"),
                duration=int(self.try_get_info("GST"))
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
            duration=5,
            role_name=self.real_saa,
            event="Guest Feedback (20s/P)"
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

        # prepared session
        if self.have_prepared_speech:
            agenda.append_session(self.prepared_session(agenda.current_datetime))

        # table topic session
        # agenda.append_session(self.table_topic_session(agenda.current_datetime))

        agenda.append_session(self.evaluation_session(agenda.current_datetime))
        agenda.dump(output_path)


class ToastmasterAgendaGenerator:
    def __init__(self, current_year=None):
        # from path_util import PathUtil
        # with open(PathUtil().get_config_path("time_dict"), "r", encoding="utf-8") as time_dict_file:
        #     self.time_dict = json.load(time_dict_file)
        #     time_dict_file.close()
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
            line = line.replace("：", ":")
            m = re.match(r"^([0-9]+)/([0-9]+)", line)
            if m is not None:
                if meeting_info is not None:
                    meetings.append(meeting_info)
                meeting_info = Meeting(
                    month=int(m.group(1)),
                    day=int(m.group(2)),
                    year=year,
                    is_english=True # (m.group(3) == "English")
                )
            elif line.find(":") != -1:
                ti = line.find(":")
                if line[:ti].strip().lower() == "skip":
                    meeting_info._skip_dict.add(cls.strip_name(line[ti+1:]).lower())
                else:
                    meeting_info.set_info(line[:ti].strip(), cls.strip_name(line[ti+1:]))

        if meeting_info is not None:
            meetings.append(meeting_info)
        return meetings

    def generate_agenda(self, call_role_path=None, member_info_path=None, update_member_info=False, log_agenda=False):
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

            agenda_path = self.path_util.get_output_path("agenda.html")
            next_meeting.to_agenda(agenda_path)
            import shutil
            agenda_backup_path = self.path_util.get_log_path("{0}.agenda.html".format(next_meeting.date_str))
            if log_agenda is True:
                shutil.copy2(agenda_path, agenda_backup_path)

            if update_member_info is False:
                member_info_lib.dump(self.path_util.get_output_path(
                    "{0}.member_info.json".format(next_meeting.date_str)))

        if update_member_info is True:
            member_info_lib.dump()

def to_agenda(yaml_path, output_path):
    import yaml
    with open(yaml_path, encoding='utf-8') as fin:
        meeting = yaml.safe_load(fin)
    theme = meeting['theme']
    language = meeting['language']
    date = meeting['date']
    year, month, day = date.split('/')
    agenda = Agenda(language, theme, 3, meeting['location'])

    curr_time = datetime.datetime(int(year), int(month), int(day), 18, 45)

    if language in meeting['role_names'].keys():
        meeting['role_names'] = meeting['role_names'][language]
    else:
        meeting['role_names'] = meeting['role_names']['default']

    for s in meeting['sessions']:
        if 'skip' in s.keys() and s['skip']:
            continue
        session = Session(curr_time, title=s['title'], lang=language)
        session.from_data(s['events'], meeting['roles'], meeting['role_names'])
        curr_time = session._current_time
        agenda.append_session(session)
    agenda.dump(output_path)
    # log
    date_str =  "{2}{0:02}{1:02}".format(
            int(month),
            int(day),
            int(year)
        )
    path_util = PathUtil()
    import shutil
    shutil.copy2(yaml_path,
        path_util.get_log_path("{0}.meeting.yaml".format(date_str)))

    agenda_path = path_util.get_output_path("agenda.html")
    agenda_backup_path = path_util.get_log_path("{0}.agenda.html".format(date_str))
    shutil.copy2(agenda_path, agenda_backup_path)

def __main__():
    if len(sys.argv) == 3:
        _, current_log_path, call_role_path = sys.argv
        raise NotImplementedException()
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(call_role_path, current_log_path, update_member_info=True)
    elif len(sys.argv) == 1:
        to_agenda(PathUtil().meeting_yaml_path, PathUtil().get_output_path("agenda.html"))
        # for root, _, files in os.walk(PathUtil().get_log_path("")):
        #     files = sorted(filter(lambda x: x.endswith(".txt"), files))
        #     for i, file in enumerate(files):
        #         generator = ToastmasterAgendaGenerator(file[:4])
        #
        #         generator.generate_agenda(
        #             call_role_path=path.join(root, file),
        #             update_member_info=True,
        #             log_agenda=(i == len(files)-1)
        #         )
    else:
        git_token = sys.argv[1]
        to_agenda(PathUtil().meeting_yaml_path, PathUtil().get_output_path("agenda.html"))
        status = subprocess.check_output(["git", "status"]).decode("utf-8")
        print(status)
        if status.find("data/member_info.json") != -1:
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
                "https://htmlpreview.github.io/?https://github.com/nyanyanya/ms-toastmaster/blob/"
                "{}/agenda_generator/output/agenda.html".format(current_branch)
            ])
            run = subprocess.run([
                "git", "remote", "set-url", "origin",
                "https://{}@github.com/nyanyanya/ms-toastmaster.git".format(git_token)
            ])
            run = subprocess.run(["git", "push"])
            print(run.stderr)
            print(run.stdout)


if __name__ == "__main__":
    __main__()
