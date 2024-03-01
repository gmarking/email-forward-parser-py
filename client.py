import json
from email.charset import QP, Charset
from email.message import EmailMessage, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser

from forward_parser import MailboxResult, ReadResult, ReadResultEmail, read


class EmailParserClient:
    """Client for calling forward parser API."""

    def get_original_eml(self, file_path: str) -> str:
        msg = self._parse_file(file_path)
        original_metadata = self._get_read_result(msg)
        return self._get_json(msg, original_metadata.email, original_metadata.forwarded)

    def get_original_metadata(self, file_path: str) -> ReadResult:
        msg = self._parse_file(file_path)
        return self._get_read_result(msg)

    def _get_json(self, message: Message, email: ReadResultEmail, forwarded: bool) -> str:
        result = {}
        if forwarded:
            result["Send-To"] = message.get("To")
            result["eml"] = message.as_string()
        else:
            result["Send-To"] = email.from_.address
            result["eml"] = self._build_original_email(email, message)
        return json.dumps(result)

    def _build_original_email(self, metadata: ReadResultEmail, message: Message) -> str:
        if not message.is_multipart():
            result_message = EmailMessage()
            self._set_headers(result_message, metadata)
            result_message.set_content(metadata.body)
            return result_message.as_string()

        result_message = MIMEMultipart('alternative')

        cs = Charset("UTF-8")
        cs.body_encoding = QP
        result_message.attach(MIMEText(metadata.body, "plain", _charset=cs))
        payload = message.get_payload()
        if isinstance(payload, list):
            for part in payload:
                if (part.get_content_type() == 'text/plain'
                        and 'attachment' not in str(part.get('Content-Disposition'))):
                    continue
                result_message.attach(part)
        return result_message.as_string()

    def _set_headers(self, message: MIMEMultipart | EmailMessage, metadata: ReadResultEmail) -> None:
        message["Date"] = metadata.date
        message["Subject"] = metadata.subject
        message["From"] = metadata.from_.address
        message["To"] = self._format_addresses(metadata.to)
        if metadata.cc:
            message["CC"] = self._format_addresses(metadata.cc)

    def _format_addresses(self, contacts: list[MailboxResult]) -> str:
        result = contacts[0].address
        for index in range(1, len(contacts)):
            result += ", " + contacts[index].address
        return result

    def _get_read_result(self, message: Message) -> ReadResult:
        body = self._get_body(message)
        subject = self._get_subject(message)
        if subject is not None:
            return read(body.strip(), subject.strip())
        return read(body.strip())

    def _get_body(self, msg: Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))

                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                    body = part.get_payload()
                    break
        else:
            body = msg.get_payload()

        return body if isinstance(body, str) else ""

    def _get_subject(self, msg: Message) -> str:
        subject = msg.get("Subject")
        return subject if subject is not None else ""

    def _parse_file(self, file_name: str) -> Message:
        with open(file_name, "r", encoding="utf8") as file:
            return Parser().parse(file)
