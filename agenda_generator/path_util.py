from os import path


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

    def get_config_path(self, config_name) -> str:
        assert config_name in ["learning_path", "roles", "time_dict", "localization"]
        return path.join(self.current_dir, "config", "{}.json".format(config_name))

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
    def meeting_yaml_path(self):
        return path.join(self.current_dir, "data", "meeting.yaml")
