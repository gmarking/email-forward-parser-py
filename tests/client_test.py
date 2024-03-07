from emailforwardparser.client import EmailParserClient

# case 1: forwarded email
# case 2: non-forwarded, eml containing email
# case 3: non-forwarded, eml non-containing email

case_1 = """Content-Type: multipart/mixed; boundary="===============7483602508082330894=="
MIME-Version: 1.0
Date: Thu, Feb 15, 2024 at 5:23=E2=80=AFPM
From: jon_doe@example.com
Subject: Test Email
To: mary_doe@example.com

--===============7483602508082330894==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

Hello,
This is a test email.
Best,
Jon
--===============7483602508082330894==
Content-Type: text/html; charset="UTF-8"
Content-Transfer-Encoding: quoted-printable

<div dir=3D"ltr"><br><br><div class=3D"gmail_quote"><div dir=3D"ltr" class=
=3D"gmail_attr">---------- Forwarded message ---------<br>From: <strong cla=
ss=3D"gmail_sendername" dir=3D"auto">Jane Doe</strong> <span dir=3D"=
auto">&lt;<a href=3D"mailto:jane_doe@example.com">jane_doe@example.com=
</a>&gt;</span><br>Date: Thu, Feb 15, 2024 at 5:23=E2=80=AFPM<br>Subject: =
Test Email<br>To: Mary Doe &lt;<a href=3D"mailto:mary_doe@example.co=
m">marry_doe@example.com</a>&gt;<br></div><br><br><div dir=3D"ltr">Hello,=C2=A0=
<div>This is a test email.</div><div>Best,=C2=A0</div><div>Jon</div></d=
iv>
</div></div>

--===============7483602508082330894==--"""

case_2_3 = """MIME-Version: 1.0
Date: Thu, 29 Feb 2024 14:51:03 -0800
Message-ID: <CA+dFi1QfRrQtDX4HVPFavejbj6cVqCH6hufLfjgVFvwdophi7w@mail.example.com>
Subject: blah
From: Jane Doe <jane_doe@example.com>
To: Jane Doe <jane_doe@example.com>, sally_doe@example.com
Content-Type: multipart/alternative; boundary="00000000000013539606128d184f"

--00000000000013539606128d184f
Content-Type: text/plain; charset="UTF-8"

multiple to email

--00000000000013539606128d184f
Content-Type: text/html; charset="UTF-8"

<div dir="ltr">multiple to email</div>

--00000000000013539606128d184f--
"""


def test_get_original_eml_case_1(mocker):
    client = EmailParserClient()
    mocker.patch("email.message.Message.as_string", return_value=case_1)
    expected_send_to = "mary_doe@example.com"
    data = client.get_original_eml_from_file("fixtures/forwarded.eml")
    assert data["Send-To"] == expected_send_to
    assert data["eml"] == case_1


def test_get_original_eml_case_2(mocker):
    client = EmailParserClient()
    mocker.patch("email.message.Message.as_string", return_value=case_2_3)
    expected_send_to = "jane_doe@example.com"
    data = client.get_original_eml_from_file("fixtures/non_forwarded_eml_attached.eml")
    assert data["Send-To"] == expected_send_to
    assert data["eml"] == case_2_3


def test_get_original_eml_case_3(mocker):
    client = EmailParserClient()
    mocker.patch("email.message.Message.as_string", return_value=case_2_3)
    expected_send_to = "jane_doe@example.com"
    data = client.get_original_eml_from_file("fixtures/nonforward.eml")
    assert data["Send-To"] == expected_send_to
    assert data["eml"] == case_2_3
