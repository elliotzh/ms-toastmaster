import json
import openpyxl
import re
import datetime
from openpyxl.drawing.image import Image
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import sys
import os
from os import path
from pathlib import PurePath


def min_distance(word1, word2):
    """
    :type word1: str
    :type word2: str
    :rtype: int
    """
    dp_matrix = list(range(0, len(word2) + 1))
    for end_index1 in range(1, len(word1) + 1):
        dp_row = [end_index1]
        dp_matrix.append(dp_row)
        for end_index2 in range(1, len(word2) + 1):
            candidate_list = [
                dp_matrix[end_index1][end_index2 - 1] + 1,
                dp_matrix[end_index1 - 1][end_index2] + 1
            ]
            # replace the last char in word1
            if word1[end_index1 - 1] == word2[end_index2 - 1]:
                candidate_list.append(dp_matrix[end_index1 - 1][end_index2 - 1])
            else:
                candidate_list.append(dp_matrix[end_index1 - 1][end_index2 - 1] + 1)
            dp_row.append(min(candidate_list))
    return dp_matrix[len(word1)][len(word2)]


def try_get_str(s):
    return str(s) if s is not None else ""


def cover_border(base_border, top=None, bottom=None, left=None, right=None):
    return Border(
        top=base_border.top if top is None else top,
        bottom=base_border.bottom if bottom is None else bottom,
        left=base_border.left if left is None else left,
        right=base_border.right if right is None else right,
    )


def style_range(ws, cell_range, border=Border()):
    """
    Apply styles to a range of cells as if they were a single cell.

    :param ws:  Excel worksheet instance
    :param cell_range: An excel range to style (e.g. A1:F20)
    :param border: An openpyxl Border
    :param fill: An openpyxl PatternFill or GradientFill
    """

    rows = ws[cell_range]
    for cell in rows[0]:
        cell.border = cover_border(cell.border, top=border.top)
    for cell in rows[-1]:
        cell.border = cover_border(cell.border, bottom=border.bottom)

    for row in rows:
        l = row[0]
        r = row[-1]
        l.border = cover_border(l.border, left=border.left)
        r.border = cover_border(r.border, right=border.right)


def set_active_sheet_by_name(wb, sheet_name):
    for s in range(len(wb.sheetnames)):
        if wb.sheetnames[s] == sheet_name:
            wb.active = s
            return True
    return False


class MemberInfo:
    def __init__(self, member_info):
        self._english_name = member_info["English Name"]
        self._chinese_name = member_info["Chinese Name"]
        self._role_records = sorted(member_info["Role Records"], key=lambda x: x["Date"])
        self._speech_records = sorted(member_info["Speech Records"], key=lambda x: x["Date"])
        for speech in self._speech_records:
            if speech["Level"].startswith("Level"):
                speech["Type"] = "pathway"
            else:
                speech["Type"] = "CC"

    def to_dict(self):
        return {
            "English Name": self._english_name,
            "Chinese Name": self._chinese_name,
            "CC Level": self.cc_level,
            "CC Level Title": self.title,
            "Pathway Level": self.pathway_level,
            "Role Records": self._role_records,
            "Speech Records": self._speech_records
        }

    @property
    def english_name(self):
        return self._english_name

    @property
    def chinese_name(self):
        return self._chinese_name

    @property
    def title(self):
        if self.cc_level is None or self.cc_level.startswith("CC"):
            return None
        else:
            return "CL"

    @property
    def cc_level(self):
        level = None
        for speech in self._speech_records:
            if speech["Type"] == "CC":
                level = speech["Level"]
        return level

    @property
    def pathway_level(self):
        level = None
        for speech in self._speech_records:
            if speech["Type"] == "pathway":
                level = speech["Level"]
        return level

    @property
    def level(self):
        return self._speech_records[-1]["Level"] if len(self._speech_records) > 0 else ""

    @property
    def is_on_pathway(self):
        return len(self._speech_records) is 0 or self._speech_records[-1]["Type"] == "pathway"

    def clear_records(self, date_str):
        if len(self._speech_records) > 0 and self._speech_records[-1]["Date"] >= date_str:
            self._speech_records = list(filter(
                lambda x: x["Date"] < date_str,
                self._speech_records
            ))

        if len(self._role_records) > 0 and self._role_records[-1]["Date"] >= date_str:
            self._role_records = list(filter(
                lambda x: x["Date"] < date_str,
                self._role_records
            ))

    def take_role(self, role_name, date_str, topic, generator):
        if role_name.find("Speaker") is 0:
            if self.is_on_pathway is True:
                self._speech_records.append({
                    "Level": generator.pathways[generator.pathways.index(self.pathway_level) + 1],
                    "Date": date_str,
                    "Topic": topic,
                    "Type": "pathway"
                })
            else:
                self._speech_records.append({
                    "Level": generator.CCs[generator.CCs.index(self.cc_level) + 1],
                    "Date": date_str,
                    "Topic": topic,
                    "Type": "CC"
                })
            return self.level
        elif role_name == "Toastmaster":
            self._role_records.append({
                "Role": role_name,
                "Date": date_str,
                "Topic": topic
            })
        elif role_name not in ["SAA", "President", "VPM"]:
            self._role_records.append({
                "Role": role_name,
                "Date": date_str
            })
        return None


class PathUtil:
    def __init__(self):
        pass

    @property
    def current_dir(self):
        return path.abspath(path.join(path.abspath(__file__), ".."))

    def get_template(self, name: str):
        return path.join(self.current_dir, "templates", name)

    @property
    def default_template_path(self) -> str:
        return self.get_template("ToastMaster_Template.xlsx")

    def get_output_path(self, name) -> str:
        return path.join(self.current_dir, "output", name)

    def get_log_path(self, name) -> str:
        return path.join(self.current_dir, "log", name)

    @property
    def default_agenda_output_path(self) -> str:
        return path.join(self.current_dir, "output", "agenda.xlsx")

    @property
    def default_config_path(self) -> str:
        return path.join(self.current_dir, "config.json")

    def get_image(self, name):
        return path.join(self.current_dir, "img", name)

    def get_vote_qr(self, speech_count: int):
        assert 1 <= speech_count <= 3
        return self.get_image("qrcode-vote-{}.png".format(speech_count))

    @property
    def club_qr(self):
        return self.get_image('qrcode-club.png')

    @property
    def club_icon(self):
        return self.get_image("icon-club.png")

    @property
    def default_meeting_info_path(self):
        return path.join(self.current_dir, "data", "meeting.txt")

    @property
    def default_member_info_path(self):
        return path.join(self.current_dir, "data", "member_info.json")


class MemberInfoLibrary:
    def __init__(self, member_info_path=None):
        self._member_info_path = PathUtil().default_member_info_path if member_info_path is None else member_info_path

        with open(self._member_info_path, "r", encoding="utf-8") as member_info_file:
            self._member_info_list = list(map(
                lambda x: MemberInfo(x),
                json.load(member_info_file)
            ))
            member_info_file.close()

    def dump(self, member_info_path=None):
        with open(self._member_info_path if member_info_path is None else member_info_path, "w", encoding="utf-8"
                  ) as member_info_file:
            json.dump(list(map(
                lambda x: x.to_dict(),
                self._member_info_list
            )), member_info_file, indent=2)

    def find(self, role_taker_name) -> MemberInfo:
        if len(role_taker_name) is not 0:
            for member_info in self._member_info_list:
                if member_info.english_name.lower().find(role_taker_name.lower()) is not -1 or \
                        member_info.chinese_name.lower().find(role_taker_name.lower()) is not -1:
                    return member_info
        else:
            return MemberInfo({
                "English Name": "TBD",
                "Chinese Name": "TBD",
                "Speech Records": [],
                "Role Records": [],
            })

        role_taker = MemberInfo({
            "English Name": role_taker_name,
            "Chinese Name": role_taker_name,
            "Speech Records": [],
            "Role Records": [],
        })
        self._member_info_list.append(role_taker)
        return role_taker

    def clear_records(self, date_str):
        for member in self._member_info_list:
            member.clear_records(date_str)


class ToastmasterAgendaGenerator:
    def __init__(self, current_year=None):
        self.roles = [
        ]

        self.pathways = [
        ]

        self.CCs = [
        ]

        self.time_dict = {
        }
        self._current_year = current_year
        self.load_settings(self.path_util.default_config_path)

    @property
    def path_util(self):
        return PathUtil()

    @classmethod
    def strip_name(cls, member_name: str):
        return re.sub(r"[\ud83c\ufe0f\udf3f\u5973\u795e\u7537]|(\[.*])|(N/A)", "", member_name).strip()

    @classmethod
    def read_info_from_call_role(cls, call_role_text):
        meetings = []
        meeting_info = {}
        for line in call_role_text.split('\n'):
            if line.find("Call Role") is not -1:
                meetings.append(meeting_info)
                meeting_info = {}

            if line.find(":") is not -1:
                ti = line.find(":")
                role_name, member_name = line[:ti], line[ti+1:]

                meeting_info[role_name.strip()] = cls.strip_name(member_name)
            else:
                line = line.replace(u"中文", "Chinese")
                m = re.match(r"([0-9]+)/([0-9]+) *\((Chinese|English)\)", line)
                if m is not None:
                    meeting_info["month"] = int(m.group(1))
                    meeting_info["day"] = int(m.group(2))
                    meeting_info["language"] = m.group(3)

        meeting_info["speech_count"] = 0
        for i in range(1, 4):
            if "SP{0}".format(i) in meeting_info and len(meeting_info["SP{0}".format(i)].strip()) is not 0:
                meeting_info["speech_count"] += 1

        meetings.append(meeting_info)
        meetings = list(filter(
            lambda x: len(x) is not 0,
            meetings
        ))
        return meetings

    def get_date_str(self, next_meeting):
        return "{2}{0:02}{1:02}".format(
            next_meeting["month"],
            next_meeting["day"],
            datetime.datetime.now().year if self._current_year is None else self._current_year
        )

    def set_role(self, next_meeting, role_sheet, member_info_lib: MemberInfoLibrary):
        speech_levels = []
        for i in range(0, len(self.roles)):
            row_index = i + 2
            current_role = self.roles[i]
            if "nick" not in current_role:
                current_role["nick"] = current_role["name"]

            role_taker_name = ""
            if current_role['nick'] in next_meeting:
                role_taker_name = next_meeting[current_role['nick']]
            if len(role_taker_name) is 0 and "default_taker" in current_role:
                role_taker_name = current_role["default_taker"]

            role_taker = member_info_lib.find(role_taker_name)
            if role_taker is not None:
                name = role_taker.english_name if next_meeting["language"] == "English" else role_taker.chinese_name
                role_sheet['B{0}'.format(row_index)] = name
                role_sheet['C{0}'.format(row_index)] = role_taker.level
                role_sheet['D{0}'.format(row_index)] = try_get_str(role_taker.title)

                topic = next_meeting["Theme"]
                if current_role["name"].startswith("Speaker"):
                    try:
                        topic = next_meeting["SP{0} Topic".format(current_role["name"][-1])]
                    except KeyError:
                        pass

                speech_level = role_taker.take_role(current_role["name"], self.get_date_str(next_meeting), topic, self)
                if speech_level is not None:
                    speech_levels.append(speech_level)

        return speech_levels

    def load_settings(self, settings_path):
        settings = json.load(open(settings_path, "r", encoding="utf-8"))
        for var in settings:
            setattr(self, var, settings[var])

    def generate_agenda(self, call_role_path=None, member_info_path=None, update_member_info=False):
        if call_role_path is None:
            call_role_path = self.path_util.default_meeting_info_path
        member_info_lib = MemberInfoLibrary(member_info_path)
        origin_text = open(call_role_path, "r", encoding="utf-8").read()

        for next_meeting in self.read_info_from_call_role(origin_text):
            member_info_lib.clear_records(self.get_date_str(next_meeting))

            with open(
                self.path_util.get_log_path("{0}.call_role.txt".format(self.get_date_str(next_meeting))),
                "w",
                encoding="utf-8"
            ) as meeting_log_file:
                meeting_log_file.write(origin_text)
                meeting_log_file.close()
            print(json.dumps(next_meeting, indent=2))
            xlsx_template = openpyxl.load_workbook(self.path_util.default_template_path)
            role_sheet = xlsx_template["Roles"]

            speech_levels = self.set_role(next_meeting, role_sheet, member_info_lib)

            is_english = next_meeting["language"] == "English"
            agenda_sheet_prefix = "Agenda" if is_english else "Chinese Agenda"
            speech_count = next_meeting["speech_count"]

            if speech_count > 0:
                agenda_sheet_name = "{0}-{1}".format(agenda_sheet_prefix, speech_count)
                agenda_sheet = xlsx_template[agenda_sheet_name]
                set_active_sheet_by_name(xlsx_template, agenda_sheet_name)

                speech_rows = [27, 29, 31]
                if is_english is True:
                    agenda_sheet["A8"] = "Theme Today: {0}".format(next_meeting["Theme"])
                else:
                    agenda_sheet["A8"] = "本期主题:  “{0}”".format(next_meeting["Theme"])

                for i in range(0, speech_count):
                    agenda_sheet["C{0}".format(speech_rows[i])] = next_meeting["SP{0} Topic".format(i + 1)]
                    current_level = speech_levels[i]
                    if current_level not in self.time_dict:
                        self.time_dict[current_level] = ["0:06", "4-6", 4, 5, 6]
                    duration, time_range, green_time, yellow_time, red_time = self.time_dict[current_level]
                    reorg = [time_range, green_time, yellow_time, red_time, duration]
                    for j in range(0, len(reorg)):
                        agenda_sheet["{0}{1}".format(chr(ord('E') + j), speech_rows[i])] = reorg[j]

                icon_img = Image(self.path_util.club_icon)
                icon_img.anchor = 'A1'
                agenda_sheet.add_image(icon_img)

                qr_img = Image(self.path_util.club_qr)
                qr_img.anchor = 'G1'
                agenda_sheet.add_image(qr_img)

                qr_img = Image(self.path_util.get_vote_qr(speech_count))
                qr_img.anchor = 'E{0}'.format(4 * speech_count + 34)
                agenda_sheet.add_image(qr_img)

                side = Side(border_style="medium", color='000000')
                border = Border(
                    left=side,
                    right=side,
                    top=side,
                    bottom=side,
                )
                style_range(agenda_sheet, 'A1:J3', border)
                style_range(agenda_sheet, 'A4:J5', border)
                style_range(agenda_sheet, 'A8:J8', border)
                style_range(agenda_sheet, 'A20:J20', border)
                style_range(agenda_sheet, 'A25:J25', border)
                style_range(agenda_sheet, 'A{0}:J{0}'.format(26 + 3 * speech_count), border)

                xlsx_template.save(self.path_util.default_agenda_output_path)
            if update_member_info is False:
                member_info_lib.dump(self.path_util.get_output_path(
                    "{0}.member_info.json".format(self.get_date_str(next_meeting))))

        if update_member_info is True:
            member_info_lib.dump()


def __main__():
    if len(sys.argv) == 3:
        _, current_log_path, call_role_path = sys.argv
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(call_role_path, current_log_path)
    # elif len(sys.argv) == 1:
    #     for root, _, files in os.walk(PathUtil().get_log_path("")):
    #         files = sorted(filter(lambda x: x.endswith(".txt"), files))
    #         for file in files:
    #             generator = ToastmasterAgendaGenerator(file[:4])
    #
    #             generator.generate_agenda(
    #                 call_role_path=path.join(root, file),
    #                 update_member_info=True
    #             )
    else:
        generator = ToastmasterAgendaGenerator()
        generator.generate_agenda(update_member_info=True)


if __name__ == "__main__":
    __main__()
