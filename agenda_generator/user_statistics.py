from member import MemberInfoLibrary, MemberInfo


def init_mentor_relationship():
    member_lib = MemberInfoLibrary()
    mentor_dict = {
        "Bill": ["Harper", "Pan", "Zhiwei"],
        "Bonnie": ["Locke", "Madison", "Shuhan", "Davie"],
        "Elliot": ["Marrisa"],
        "Harper": ["Elliot"],
        "Nancy": ["Bill"],
        "Raymond Lu": ["Fengling", "Haoyu", "Joey", "Kay"]
    }
    for mentor_name in mentor_dict:
        for mentee_name in mentor_dict[mentor_name]:
            member_lib.find(mentee_name).set_mentor(mentor_name, member_lib)
    member_lib.dump()


def __main__():
    init_mentor_relationship()
    # member_lib = MemberInfoLibrary()
    # member_lib.dump()
    pass


if __name__ == "__main__":
    __main__()