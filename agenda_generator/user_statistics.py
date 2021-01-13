from member import MemberInfoLibrary, MemberInfo


def init_mentor_relationship():
    member_lib = MemberInfoLibrary()
    mentor_dict = {
        "Bill": ["Harper", "Pan", "Zhiwei", "Eilleen"],
        "Bonnie": ["Locke", "Madison", "Shuhan", "Davie"],
        "Elliot": ["Marrisa"],
        "Davie": ["Sawyer"],
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
    member_lib = MemberInfoLibrary()
    rows = []
    for user_name in [
        "Bill", "Harper", "Pan", "Zhiwei",
        "Bonnie", "Locke", "Madison", "Shuhan", "Davie",
        "Davie", "Sawyer",
        "Elliot", "Marrisa", "Eilleen",
        "Harper", "Elliot",
        "Nancy", "Bill",
        "Raymond Lu", "Fengling", "Haoyu", "Joey", "Kay",
        "TBD", "Annie Liu", "Bonnie", "Brenda", "Julia", "Nancy", "Raymond Lu", "Alicia"
    ]:
        rows.append(member_lib.find(user_name).to_statistics_row())
    columns = list(rows[0])
    for row in rows:
        print(",".join(map(lambda x: str(row[x]), columns)))


if __name__ == "__main__":
    __main__()