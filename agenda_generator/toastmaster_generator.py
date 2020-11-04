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
from agenda import Agenda


def try_get_str(s):
    return str(s) if s is not None else ""


class Meeting:
    def __init__(self, month: int, day: int, is_english: bool, year=None):
        self._function_role_taker = {}  # type: Dict[str, MemberInfo]
        self._info = {}  # type: Dict[str, str]
        self._year = year if year is not None else 2020
        self._month = month
        self._day = day
        self._is_english = is_english
        self._theme = "TBD"
        self._speakers = []  # type: List[MemberInfo]

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
            datetime.datetime.now().year if self._year is None else self._year
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
            "origin_info": self._info,
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
        self._theme = self.try_get_info("Theme")

        for i in range(1, 5):
            speaker_name = self.try_get_info("SP{}".format(i))
            speech_topic = self.try_get_info("SP{} Topic".format(i))
            if len(speaker_name) is not 0:
                role_taker = member_lib.assign_role(
                    speaker_name,
                    "Speaker{}".format(i),
                    self.date_str,
                    topic=speech_topic
                )

                self._speakers.append(role_taker)

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

    def to_agenda(self, output_path):
        agenda = Agenda(self.language)
        agenda.dump(output_path)

        # xlsx_template = openpyxl.load_workbook()
        # role_sheet = xlsx_template["Roles"]
        #
        # speech_levels = self.set_role(self, role_sheet, member_info_lib)
        #
        # is_english = self
        # agenda_sheet_prefix = "Agenda" if is_english else "Chinese Agenda"
        # speech_count = self["speech_count"]
        #
        # if speech_count > 0:
        #     agenda_sheet_name = "{0}-{1}".format(agenda_sheet_prefix, speech_count)
        #     agenda_sheet = xlsx_template[agenda_sheet_name]
        #     set_active_sheet_by_name(xlsx_template, agenda_sheet_name)
        #
        #     speech_rows = [27, 29, 31]
        #     if is_english is True:
        #         agenda_sheet["A8"] = "Theme Today: {0}".format(self["Theme"])
        #     else:
        #         agenda_sheet["A8"] = "本期主题:  “{0}”".format(self["Theme"])
        #
        #     for i in range(0, speech_count):
        #         agenda_sheet["C{0}".format(speech_rows[i])] = self["SP{0} Topic".format(i + 1)]
        #         current_level = speech_levels[i]
        #         if current_level not in self.time_dict:
        #             self.time_dict[current_level] = self.time_dict['default']
        #         duration, time_range, green_time, yellow_time, red_time = self.time_dict[current_level]
        #         reorg = [time_range, green_time, yellow_time, red_time, duration]
        #         for j in range(0, len(reorg)):
        #             agenda_sheet["{0}{1}".format(chr(ord('E') + j), speech_rows[i])] = reorg[j]
        #
        #     icon_img = Image(self.path_util.club_icon)
        #     icon_img.anchor = 'A1'
        #     agenda_sheet.add_image(icon_img)
        #
        #     qr_img = Image(self.path_util.club_qr)
        #     qr_img.anchor = 'G1'
        #     agenda_sheet.add_image(qr_img)
        #
        #     qr_img = Image(self.path_util.get_vote_qr(speech_count))
        #     qr_img.anchor = 'E{0}'.format(4 * speech_count + 34)
        #     agenda_sheet.add_image(qr_img)
        #
        #     side = Side(border_style="medium", color='000000')
        #     border = Border(
        #         left=side,
        #         right=side,
        #         top=side,
        #         bottom=side,
        #     )
        #     style_range(agenda_sheet, 'A1:J3', border)
        #     style_range(agenda_sheet, 'A4:J5', border)
        #     style_range(agenda_sheet, 'A8:J8', border)
        #     style_range(agenda_sheet, 'A20:J20', border)
        #     style_range(agenda_sheet, 'A25:J25', border)
        #     style_range(agenda_sheet, 'A{0}:J{0}'.format(26 + 3 * speech_count), border)
        #
        #     xlsx_template.save(self.path_util.default_agenda_output_path)



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
    def read_info_from_call_role(cls, call_role_text):
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
                    is_english=(m.group(3) == "English")
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

        for next_meeting in self.read_info_from_call_role(origin_text):
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

            next_meeting.to_agenda()

            if update_member_info is False:
                member_info_lib.dump(self.path_util.get_output_path(
                    "{0}.member_info.json".format(next_meeting.date_str)))

        if update_member_info is True:
            member_info_lib.dump()


def __main__():
    if len(sys.argv) == 3:
        _, current_log_path, call_role_path = sys.argv
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(call_role_path, current_log_path)
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
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(["git", "commit", "-m", "feat: auto-generated change"])
            run = subprocess.run([
                "git", "remote", "set-url", "origin",
                "https://{}@github.com/eliiotz/ms-toastmaster.git".format(git_token)
            ])
            run = subprocess.run(["git", "push"])
            print(run.stderr)
            print(run.stdout)


if __name__ == "__main__":
    __main__()
