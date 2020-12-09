import json
from path_util import PathUtil
from os import path
from typing import List, Optional


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


class MemberInfo:
    def __init__(self, member_info):
        self._english_name = member_info["English Name"]
        self._chinese_name = member_info["Chinese Name"]
        self._role_records = sorted(member_info["Role Records"], key=lambda x: x["Date"])
        self._speech_records = sorted(member_info["Speech Records"], key=lambda x: x["Date"])
        self.nick_names = [] if "Nick Names" not in member_info else member_info["Nick Names"]

        if "Current Level" in member_info:
            self._current_level = member_info["Current Level"]
        else:
            self.reset_level()

        for speech in self._speech_records:
            if speech["Level"].startswith("Level"):
                speech["Type"] = "pathway"
            else:
                speech["Type"] = "CC"

    def reset_level(self):
        if len(self._speech_records) > 0:
            self._current_level = self._speech_records[-1]["Level"]
        else:
            self._current_level = "NotStarted"

    def to_dict(self):
        return {
            "English Name": self._english_name,
            "Chinese Name": self._chinese_name,
            "Nick Names": self.nick_names,
            "Current Level": self.current_level,
            "Role Records": self._role_records,
            "Speech Records": self._speech_records
        }

    @property
    def english_name(self):
        return self._english_name

    @property
    def current_level(self):
        return self._current_level

    @property
    def chinese_name(self):
        return self._chinese_name

    @property
    def level(self):
        return self._speech_records[-1]["Level"] if len(self._speech_records) > 0 else "NotStarted"

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

        self.reset_level()

    def append_speech(self, new_level, date_str, topic, speech_type):
        self._current_level = new_level
        self._speech_records.append({
            "Level": new_level,
            "Date": date_str,
            "Topic": topic,
            "Type": speech_type
        })

    def take_function_role(self, role_name, date_str, topic):
        if role_name in ["TTM", "Toastmaster"]:
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

    @property
    def last_speech_topic(self) -> str:
        return self._speech_records[-1]["Topic"]


class MemberInfoLibrary:
    def __init__(self, member_info_path=None):
        self._path_util = PathUtil()

        self._member_info_path = path.join(self._path_util.current_dir, "data", "member_info.json") \
            if member_info_path is None else member_info_path

        with open(self._member_info_path, "r", encoding="utf-8") as member_info_file:
            self._member_info_list = list(map(
                lambda x: MemberInfo(x),
                json.load(member_info_file)
            ))
            member_info_file.close()

        with open(self._path_util.get_config_path("learning_path"), "r", encoding="utf-8") as in_file:
            learning_path = json.load(in_file)
            in_file.close()

        self._pathway_path = learning_path["pathway"]  # type: List[str]
        self._cc_path = learning_path["CC"]

    def dump(self, member_info_path=None):
        with open(self._member_info_path if member_info_path is None else member_info_path, "w", encoding="utf-8"
                  ) as member_info_file:
            json.dump(list(map(
                lambda x: x.to_dict(),
                self._member_info_list
            )), member_info_file, indent=2)

    def find(self, role_taker_name) -> MemberInfo:
        if role_taker_name is not None and len(role_taker_name) is not 0:
            for member_info in self._member_info_list:
                for name in [
                    member_info.english_name,
                    member_info.chinese_name,
                    *member_info.nick_names
                ]:
                    if name.lower().find(role_taker_name.lower()) is 0:
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

    def next_level(self, current_level: str):
        if current_level in self._pathway_path:
            return "pathway", self._pathway_path[self._pathway_path.index(current_level) + 1]
        elif current_level in self._cc_path:
            return "CC", self._cc_path[self._cc_path.index(current_level) + 1]

    def assign_role(self, role_taker_name: str, role_name: str, date_str, topic) -> MemberInfo:
        role_taker = self.find(role_taker_name)
        if role_name.find("Speaker") is 0:
            speech_type, next_level = self.next_level(role_taker.current_level)
            role_taker.append_speech(next_level, date_str, topic, speech_type)
        else:
            role_taker.take_function_role(role_name, date_str, topic)
        return role_taker


if __name__ == "__main__":
    member_lib = MemberInfoLibrary()
    user = member_lib.find("Elliot")
    print(user.to_dict())
    member_lib.assign_role("Elliot", "SP1", "20201104", "test1")
    print(user.to_dict())