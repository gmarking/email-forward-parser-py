from dataclasses import dataclass, field
from re import Pattern

from loop import loop_regexes_match, loop_regexes_replace, loop_regexes_split
from regexs import (BYTE_ORDER_MARK, CARRIAGE_RETURN, FOUR_SPACES, MAILBOX,
                    MAILBOX_ADDRESS, MAILBOX_SEPARATORS, NON_BREAKING_SPACE,
                    ORIGINAL_CC, ORIGINAL_CC_LAX, ORIGINAL_DATE,
                    ORIGINAL_DATE_LAX, ORIGINAL_FROM, ORIGINAL_FROM_LAX,
                    ORIGINAL_REPLY_TO, ORIGINAL_SUBJECT, ORIGINAL_SUBJECT_LAX,
                    ORIGINAL_TO, ORIGINAL_TO_LAX, QUOTE, QUOTE_LINE_BREAK,
                    SEPARATOR, SEPARATOR_WITH_INFORMATION, SUBJECT,
                    TRAILING_NON_BREAKING_SPACE)
from utils import (find_named_matches, preprocess_string,
                   reconciliate_split_match, trim_string)


@dataclass
class MailboxResult:
    """Class storing the name and address of a mailbox."""
    name: str = ""
    address: str = ""


@dataclass
class ParseBodyResult:
    """Class storing metadata of parsed forwarded email."""
    body: str = ""
    message: str = ""
    email: str = ""


@dataclass
class ParseOriginalEmailResult:
    """Class storing metadata of original content in forwarded message."""
    date: str = ""
    subject: str = ""
    body: str = ""
    from_: MailboxResult = field(default_factory=MailboxResult)
    to: list[MailboxResult] = field(default_factory=list)
    cc: list[MailboxResult] = field(default_factory=list)


@dataclass
class ReadResultEmail:
    # XXX: compare with ParseOriginalEmailResult and see if needed
    """Class storing metadata from read operation of email."""
    date: str = ""
    subject: str = ""
    body: str = ""
    from_: MailboxResult = field(default_factory=MailboxResult)
    to: list[MailboxResult] = field(default_factory=list)
    cc: list[MailboxResult] = field(default_factory=list)


@dataclass
class ReadResult:
    """Result object storing forwarded email metadata."""
    forwarded: bool = False
    message: str = ""
    email: ReadResultEmail = field(default_factory=ReadResultEmail)


def parse_subject(subject: str) -> str:
    match, _ = loop_regexes_match(SUBJECT, subject)
    if len(match) > 0:
        return trim_string(match[1])
    return ""


def parse_body(body: str, forwarded: bool) -> ParseBodyResult:
    body = CARRIAGE_RETURN.sub("\n", body)
    body = BYTE_ORDER_MARK.sub("", body)
    body = TRAILING_NON_BREAKING_SPACE.sub("", body)
    body = NON_BREAKING_SPACE.sub(" ", body)
    match = loop_regexes_split(SEPARATOR, body, True)
    if len(match) > 2:
        email = reconciliate_split_match(match, 3, [2], None)
        return ParseBodyResult(
            body=body,
            message=match[0].strip(),
            email=email.strip()
        )

    if forwarded:
        match = loop_regexes_split(ORIGINAL_FROM, body, True)
        if len(match) > 3:
            email = reconciliate_split_match(
                match, 4, [1, 3], lambda i: i % 3 == 2)
            return ParseBodyResult(
                body=body, message=match[0].strip(), email=email.strip()
            )

    return ParseBodyResult()


def parse_original_body(text: str) -> str:
    regexes = [ORIGINAL_SUBJECT, ORIGINAL_CC, ORIGINAL_TO, ORIGINAL_REPLY_TO]
    current = 0
    for regex in regexes:
        match = loop_regexes_split(regex, text, True)
        if len(match) > 2 and match[3].startswith("\n\n"):
            body = reconciliate_split_match(
                match, 4, [3], lambda i: i % 3 == 2)
            return body.strip()
        current += 1
    match = loop_regexes_split(
        ORIGINAL_SUBJECT + ORIGINAL_SUBJECT_LAX, text, True)
    if len(match) > 3:
        body = reconciliate_split_match(match, 4, [3], lambda i: i % 3 == 2)
        return body.strip()

    return text.strip()


def parse_original_email(text: str, body: str) -> ParseOriginalEmailResult:
    text = BYTE_ORDER_MARK.sub("", text)
    text = QUOTE_LINE_BREAK.sub("", text)
    text = QUOTE.sub("", text)
    text = FOUR_SPACES.sub("", text)

    return ParseOriginalEmailResult(
        body=parse_original_body(text),
        from_=parse_original_from(text, body),
        to=parse_original_to(text),
        cc=parse_original_cc(text),
        subject=parse_original_subject(text),
        date=parse_original_date(text, body),
    )


def parse_original_from(text: str, body: str) -> MailboxResult:
    authors = parse_mailbox(ORIGINAL_FROM, text)
    if authors:
        author = authors[0]
        if author.name or author.address:
            return author

    match, pattern = loop_regexes_match(SEPARATOR_WITH_INFORMATION, body)
    if len(match) == 4:
        named_matches = find_named_matches(pattern, body)
        return prepare_mailbox(
            named_matches.get("from_name", ""), named_matches.get(
                "from_address", "")
        )

    match, _ = loop_regexes_match(ORIGINAL_FROM_LAX, text)
    if len(match) > 1:
        name = match[2]
        address = match[3]
        return prepare_mailbox(name, address)

    return MailboxResult()


def parse_original_to(text: str) -> list[MailboxResult]:
    recipients = parse_mailbox(ORIGINAL_TO, text)
    if recipients:
        return recipients

    text = loop_regexes_replace(ORIGINAL_SUBJECT_LAX, text)
    text = loop_regexes_replace(ORIGINAL_DATE_LAX, text)
    text = loop_regexes_replace(ORIGINAL_CC_LAX, text)
    return parse_mailbox(ORIGINAL_TO_LAX, text)


def parse_original_cc(text: str) -> list[MailboxResult]:
    recipients = parse_mailbox(ORIGINAL_CC, text)
    if recipients:
        return recipients

    text = loop_regexes_replace(ORIGINAL_SUBJECT_LAX, text)
    text = loop_regexes_replace(ORIGINAL_DATE_LAX, text)
    return parse_mailbox(ORIGINAL_CC_LAX, text)


def parse_original_subject(text: str) -> str:
    match, _ = loop_regexes_match(ORIGINAL_SUBJECT, text)
    if match:
        return match[1].strip()
    match, _ = loop_regexes_match(ORIGINAL_SUBJECT_LAX, text)
    if match:
        return match[1].strip()

    return ""


def parse_original_date(text: str, body: str) -> str:
    match, _ = loop_regexes_match(ORIGINAL_DATE, text)
    if match:
        return match[1].strip()
    match, pattern = loop_regexes_match(SEPARATOR_WITH_INFORMATION, body)

    if len(match) == 4:
        named_matches = find_named_matches(pattern, body)
        return named_matches.get("date", "").strip()

    text = loop_regexes_replace(ORIGINAL_SUBJECT_LAX, text)
    match, _ = loop_regexes_match(ORIGINAL_DATE_LAX, text)
    if match:
        return match[1].strip()

    return ""


def parse_mailbox(regexes: list[Pattern], text: str) -> list[MailboxResult]:
    match, _ = loop_regexes_match(regexes, text)
    if match:
        mailboxes_line = match[-1].strip()
        if mailboxes_line:
            mailboxes = []
            while mailboxes_line:
                mailbox_match, _ = loop_regexes_match(
                    MAILBOX, mailboxes_line)
                if mailbox_match:
                    if len(mailbox_match) == 3:
                        name = mailbox_match[1]
                        address = mailbox_match[2]
                    else:
                        name = ""
                        address = mailbox_match[1]
                    mailboxes.append(prepare_mailbox(name, address))
                    mailboxes_line = mailboxes_line.replace(
                        mailbox_match[0], "", 1
                    ).strip()
                    if mailboxes_line and mailboxes_line[0] in MAILBOX_SEPARATORS:
                        mailboxes_line = mailboxes_line[1:].strip()
                else:
                    mailboxes.append(prepare_mailbox("", mailboxes_line))
                    mailboxes_line = ""
            return mailboxes
    return []


def prepare_mailbox(name: str, address: str) -> MailboxResult:
    name = name.strip()
    address = address.strip()

    match, _ = loop_regexes_match(MAILBOX_ADDRESS, address)
    if not match:
        name = address
        address = ""
    if address == name:
        name = ""
    return MailboxResult(name.strip(), address.strip())


def read(body: str, subject: str | None = None) -> ReadResult:
    email = ParseOriginalEmailResult()
    forwarded = False
    body_result = ParseBodyResult()
    parsed_subject = ""

    if subject:
        subject = preprocess_string(subject)
        parsed_subject = parse_subject(subject)
        if parsed_subject:
            forwarded = True

    if not subject or forwarded:
        body = preprocess_string(body)
        body_result = parse_body(body, forwarded)
        # print(f"body_result: {body_result}")
        if body_result.email:
            forwarded = True
            email = parse_original_email(body_result.email, body_result.body)
    subject_result = parsed_subject if parsed_subject else email.subject

    return ReadResult(
        forwarded=forwarded,
        message=body_result.message,
        email=ReadResultEmail(
            date=email.date,
            subject=subject_result,
            body=email.body,
            from_=email.from_,
            to=email.to,
            cc=email.cc,
        ),
    )
