from emailforwardparser.forward_parser import get_forwarded_metadata, ForwardMetadata
from .cases import BODY_ONLY_CASES, BODY_SUBJECT_CASES

test_subject = "Integer consequat non purus"
test_body = "Aenean quis diam urna. Maecenas eleifend vulputate ligula ac consequat. Pellentesque cursus tincidunt mauris non venenatis.\nSed nec facilisis tellus. Nunc eget eros quis ex congue iaculis nec quis massa. Morbi in nisi tincidunt, euismod ante eget, eleifend nisi.\n\nPraesent ac ligula orci. Pellentesque convallis suscipit mi, at congue massa sagittis eget."
test_message = "Praesent suscipit egestas hendrerit.\n\nAliquam eget dui dui."

test_from_address = "john.doe@acme.com"
test_from_name = "John Doe"

test_to_address_1 = "bessie.berry@acme.com"
test_to_name_1 = "Bessie Berry"
test_to_address_2 = "suzanne@globex.corp"
test_to_name_2 = "Suzanne"

test_cc_address_1 = "walter.sheltan@acme.com"
test_cc_name_1 = "Walter Sheltan"
test_cc_address_2 = "nicholas@globex.corp"
test_cc_name_2 = "Nicholas"

def get_fixtures(email_file: str, subject_file: str):
    email_path = f"fixtures/{email_file}.txt"
    subject_path = f"fixtures/{subject_file}.txt"

    with open(email_path, 'r', encoding="utf8") as file:
        email = file.read()

    subject = ""
    if subject_file:
        with open(subject_path, 'r', encoding="utf8") as file:
            subject = file.read()

    return email, subject

def read_fixture_files(email_file: str, subject_file: str):
    email, subject = get_fixtures(email_file, subject_file)
    return get_forwarded_metadata(email, subject)


def test_body_only():
    for entry in BODY_ONLY_CASES:
        result = read_fixture_files(entry, "")
        simple_asserts(entry, result)

def test_body_and_subject():
    for entry in BODY_SUBJECT_CASES:
        body, subject = entry.split(',')
        result = read_fixture_files(body, subject)
        assert result.email.subject == test_subject
        simple_asserts(entry, result)

def simple_asserts(entry: str, result: ForwardMetadata):
    assert result.forwarded is True
    assert result.email.subject == test_subject

    assert len(result.email.date) > 1
    assert result.email.from_.name == test_from_name
    assert result.email.from_.address == test_from_address

    assert len(result.message) == 0

    if not entry.startswith("outlook_2019_"):
        assert len(result.email.to) > 0

        assert len(result.email.to[0].name) == 0
        assert result.email.to[0].address == test_to_address_1

    if not entry.startswith("outlook_2019_") and not entry.startswith("ionos_one_and_one_"):
        assert len(result.email.cc) > 0
        assert result.email.cc[0].name == test_cc_name_1
        assert result.email.cc[0].address == test_cc_address_1
        assert result.email.cc[1].name == test_cc_name_2
        assert result.email.cc[1].address == test_cc_address_2
