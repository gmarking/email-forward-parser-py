import json
import re
from email.charset import QP, Charset
from email.message import EmailMessage, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import Parser

from emailforwardparser import forward_parser as fp


class EmailParserClient:
    """
    A client for parsing email messages, with support for detecting and handling forwarded emails.
    """

    def get_original_eml(self, file_path: str) -> str:
        """
        Retrieve the original email message as a JSON string, including metadata and content.

        :param file_path: The path to the email file to parse.
        :type file_path: str
        :return: A JSON string containing the email metadata and content.
        :rtype: str
        """
        msg = self._parse_file(file_path)
        original_metadata = self._get_forwarded_metadata(msg)
        if not original_metadata.forwarded:
            eml = self._get_eml_attachment(msg)
            if eml:
                original_metadata = self._get_forwarded_metadata(eml)
                msg = eml
        return self._get_json(msg, original_metadata.email, original_metadata.forwarded)

    def get_original_metadata(self, file_path: str) -> fp.ForwardMetadata:
        """
        Extract metadata from the original or forwarded email.

        :param file_path: The path to the email file to parse.
        :type file_path: str
        :return: An object containing metadata of the original email.
        :rtype: fp.ForwardMetadata
        """
        msg = self._parse_file(file_path)
        return self._get_forwarded_metadata(msg)

    def _get_json(self, message: Message, email: fp.OriginalMetadata, forwarded: bool) -> str:
        result = {}
        if forwarded:
            result["Send-To"] = email.to[0].address
            result["eml"] = self._build_original_email(email, message)
        else:
            result["Send-To"] = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', message.get("From")).group(0)
            result["eml"] = message.as_string()
        return json.dumps(result)

    def _build_original_email(self, metadata: fp.OriginalMetadata, message: Message) -> str:
        if not message.is_multipart():
            result_message = EmailMessage()
            result_message.set_payload(self._get_headers(metadata) + metadata.body)
            result_message.set_content(metadata.body)
            return result_message.as_string()

        result_message = MIMEMultipart('alternative')

        cs = Charset("UTF-8")
        cs.body_encoding = QP
        result_message.attach(MIMEText(self._get_headers(metadata) + metadata.body, "plain", _charset=cs))
        payload = message.get_payload()
        if isinstance(payload, list):
            for part in payload:
                if (part.get_content_type() == 'text/plain'
                        and 'attachment' not in str(part.get('Content-Disposition'))):
                    continue
                result_message.attach(part)
        return result_message.as_string()

    def _get_headers(self, metadata: fp.OriginalMetadata) -> str:
        result = ""
        result += "Date: " + metadata.date + "\n"
        result += "Subject: " + metadata.subject + "\n"
        result += "From: " + metadata.from_.address + "\n"
        result += "To: " + self._format_addresses(metadata.to) + "\n"
        if metadata.cc:
            result += self._format_addresses(metadata.cc) + "\n"
        return result + "\n\n"

    def _format_addresses(self, contacts: list[fp.MailboxResult]) -> str:
        result = contacts[0].address
        for index in range(1, len(contacts)):
            result += ", " + contacts[index].address
        return result

    def _get_forwarded_metadata(self, message: Message) -> fp.ForwardMetadata:
        body = self._get_body(message)
        subject = message.get("Subject")
        subject = subject if subject is not None else ""
        if subject:
            return fp.get_forwarded_metadata(body.strip(), subject.strip())
        return fp.get_forwarded_metadata(body.strip())

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

    def _get_eml_attachment(self, message: Message) -> Message | None:
        for part in message.walk():
            file_name = part.get_filename()
            if (file_name is not None and file_name.endswith(".eml")):
                return part.get_payload()[0]
        return None

    def _parse_file(self, file_name: str) -> Message:
        with open(file_name, "r", encoding="utf8") as file:
            return Parser().parse(file)
