"""
Defines classes for dealing with generic chatting (text messaging, read receipts, etc)
"""
import random
import time
import requests
import json
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from kik_unofficial.datatypes.peers import Group
from kik_unofficial.datatypes.xmpp.base_elements import XMPPElement, XMPPResponse
from kik_unofficial.utilities.parsing_utilities import ParsingUtilities


class OutgoingChatMessage(XMPPElement):
    """
    Represents an outgoing text chat message to another kik entity (member or group)
    """

    def __init__(self, peer_jid, body, is_group=False, bot_mention_jid=None):
        super().__init__()
        self.peer_jid = peer_jid
        self.body = body
        self.is_group = is_group
        self.bot_mention_jid = bot_mention_jid

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        message_type = "chat" if not self.is_group else "groupchat"
        bot_mention_data = ('<mention>'
                            '<bot>{}</bot>'
                            '</mention>').format(self.bot_mention_jid) if self.bot_mention_jid else ''
        data = ('<message type="{}" to="{}" id="{}" cts="{}">'
                '<body>{}</body>'
                '{}'
                '<preview>{}</preview>'
                '<kik push="true" qos="true" timestamp="{}" />'
                '<request xmlns="kik:message:receipt" r="true" d="true" />'
                '<ri></ri>'
                '</message>'
                ).format(message_type, self.peer_jid, self.message_id, timestamp,
                         ParsingUtilities.escape_xml(self.body), bot_mention_data,
                         ParsingUtilities.escape_xml(self.body[0:20]),
                         timestamp)
        return data.encode()


class OutgoingGroupChatMessage(OutgoingChatMessage):
    """
    Represents an outgoing text chat message to a group
    """

    def __init__(self, group_jid, body, bot_mention_jid):
        super().__init__(group_jid, body, is_group=True, bot_mention_jid=bot_mention_jid)


class OutgoingStanza(XMPPElement):
    def __init__(self, raw_xmpp: str or bytes or list[bytes]):
        super().__init__()
        self.raw_xmpp = raw_xmpp

    def serialize(self):
        if isinstance(self.raw_xmpp, str):
            return self.raw_xmpp.encode()
        else:
            return self.raw_xmpp


class OutgoingChatImage(XMPPElement):
    """
   Represents an outgoing image chat message to another kik entity (member or group)
   """

    def __init__(self, peer_jid, file_location, allow_forward, allow_save, fake_camera, is_group=False):
        super().__init__()
        self.peer_jid = peer_jid
        self.is_group = is_group
        self.parsed_image = ParsingUtilities.parse_image(file_location)
        self.timestamp = time.time()
        self.allow_forward = allow_forward
        self.allow_save = allow_save
        self.fake_camera = fake_camera

    def serialize(self):
        message_type = "chat" if not self.is_group else "groupchat"
        xmlns = "jabber:client" if not self.is_group else "kik:groups"
        timestamp = str(int(round(time.time() * 1000)))

        # Allow forward flag should always be included
        image_config = f'<allow-forward>{str(self.allow_forward).lower()}</allow-forward>'

        # Needs to be inverted
        if not self.allow_save:
            image_config += '<disallow-save>true</disallow-save>'

        # not working still shows as Gallery
        if self.fake_camera:
            app_id = "com.kik.ext.camera"
            app_name = "Camera"
        else:
            app_id = "com.kik.ext.gallery"
            app_name = "Gallery"

        data = (
            f'<message to="{self.peer_jid}" id="{self.message_id}" cts="{timestamp}" type="{message_type}" xmlns="{xmlns}">'
            f'<pb/>'
            f'<kik push="true" qos="true" timestamp="{timestamp}" />'
            f'<request xmlns="kik:message:receipt" d="true" r="true" />'
            f'<content id="{self.content_id}" app-id="{app_id}" v="2">'
            f'<strings>'
            f'<app-name>{app_name}</app-name>'
            f'<file-size>{self.parsed_image["size"]}</file-size>'
            f'{image_config}'
            f'<file-content-type>image/jpeg</file-content-type>'
            f'<file-name>{self.content_id}.jpg</file-name>'
            f'</strings>'
            f'<extras />'
            f'<hashes>'
            f'<sha1-original>{self.parsed_image["SHA1"]}</sha1-original>'
            f'<sha1-scaled>{self.parsed_image["SHA1Scaled"]}</sha1-scaled>'
            f'<blockhash-scaled>{self.parsed_image["blockhash"]}</blockhash-scaled>'
            f'</hashes>'
            f'<images>'
            f'<preview>{self.parsed_image["base64"]}</preview>'
            f'<icon>iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAARzQklUCAgICHwIZIgAAAMpSURBVGiB7ZdNSBRhGMd/M1NJhZaGlRHmIRULsmN0sGsXqUOnoEMQhF07WRB0SPuAkjBCSTzUIfDS0sEgsCw6lVQmmbrq+oHa5k7q6urqzkyHSXTdHZuvnF3Z32n2fR/m/f/3fd73eUZA04SydxxWFao1OAPkkdrIAvhEidruCvxCWbtWrCi8BEq9VmaRHkmiUlQVqkk/8QClqkK1UNKmhUj9tDFCFklf8QB5otcKnJIx4DUZA16zxWjidD5cL4a9WRspJ5FgFGr6oPVX8nnDHUgF8aBruFZsPG9oIBXEL7OelrQ/AxkDXuO6gZgG84rbbzXG8Bq1w6cpeDgIEQVO5MKVItghublCIq4ZGIrA1e8wEdV/d4Vh91a4VBgfp2owp0C2Syu7lkKd4RXxABrwdDQxbmQeqr7B2II767pmQEg2tmZQ0aBhGD5OwYMBWFKdr+uagWM5ULCq4AjAhYPxMa+C8GJCf34bgt455+s6NjC+AFEVCrdD3VE4mQvlOVBVBOcPrMT9ikJ9QN8FgJkYPArot5YTHB2l0QW4+AUuH4JzBXB8Fzwp10Vlrflrno9DIBI/9mYSWoNQuc++Bts7EFXhrh+G5/Vuse9vOkhCoviuMDQEYG3Kq0DjEPxesqvCgYGvM/Be1p/nFLjZC9NJhMzE4LYflgxSpT8Crw1aZTPYMjCvwL1+vWAt0zEFvp+JsW2T8Hna+F2KBnWDEFq0o8SGAQ1oGoHOmfhxFagbgI5VYscX4I7/3wc1tAj3B1YOuBUsGwhEoGUs+dycArf69JyOqnrqyCbzu20SematqrFhoGk4vuKu5UcYno3qKdUum3+vvASNw1bVWLhGNeCDDC3j68cpwOMhvahZ7Upbg3B2P5zak7yyJ8P0DszGoH7QXKyi6TXCDo1DEImZjze9AzsluFECIQd3thnyt1lrwU0bEAU4km1H0v8l80npNYYGgutclRvNeloMDdT0pYaJYFQvjkYIJW2aw47cWzbvGUgXMga8ZlMYsND0phyyKIDPaxV2EcAnihK1QI/XYmzQI0rUit0V+CWJSgGaSY90kgVoliQquyvw/wEBywt7TQ67XwAAAABJRU5ErkJggg==</icon>'
            f'</images>'
            f'<uris />'
            f'</content>'
            f'</message>'
        )

        packets = [data[s:s + 16384].encode() for s in range(0, len(data), 16384)]
        return list(packets)


class OutgoingChatVideo(XMPPElement):
    """
   Represents an outgoing image chat message to another kik entity (member or group)
   """

    def __init__(self, peer_jid, video_location, thumbnail_location, video_duration, allow_forward, allow_save,
                 auto_play, muted, looping, is_group):
        super().__init__()
        self.peer_jid = peer_jid
        self.is_group = is_group
        self.parsed_video = ParsingUtilities.parse_video(video_location)
        self.parsed_thumbnail = ParsingUtilities.parse_image(thumbnail_location)
        self.video_duration = video_duration
        self.allow_forward = allow_forward
        self.allow_save = allow_save
        self.auto_play = auto_play
        self.muted = muted
        self.looping = looping

    def serialize(self):
        message_type = "chat" if not self.is_group else "groupchat"
        xmlns = "jabber:client" if not self.is_group else "kik:groups"
        timestamp = str(int(round(time.time() * 1000)))

        app_id = "com.kik.ext.video-gallery"
        preview_data = self.parsed_thumbnail['base64']

        # Allow forward flag should always be included
        video_config = f'<allow-forward>{str(self.allow_forward).lower()}</allow-forward>'

        # Needs to be inverted
        if not self.allow_save:
            video_config += '<disallow-save>true</disallow-save>'
        if self.auto_play:
            video_config += '<video-should-autoplay>true</video-should-autoplay>'
        if self.muted:
            video_config += '<video-should-be-muted>true</video-should-be-muted>'
        if self.looping:
            video_config += '<video-should-loop>true</video-should-loop>'

        data = (
            f'<message to="{self.peer_jid}" id="{self.message_id}" cts="{timestamp}" type="{message_type}" xmlns="{xmlns}">'
            f'<pb/>'
            f'<kik push="true" qos="true" timestamp="{timestamp}" />'
            f'<request xmlns="kik:message:receipt" d="true" r="true" />'
            f'<content id="{self.content_id}" app-id="{app_id}" v="2">'
            f'<strings>'
            f'<app-name>Gallery</app-name>'
            f'<file-size>{self.parsed_video["size"]}</file-size>'
            f'{video_config}'
            f'<layout>video</layout>'
            f'<file-content-type>video/mp4</file-content-type>'
            f'<file-name>{self.content_id}.mp4</file-name>'
            f'<duration>{self.video_duration}</duration>'
            f'</strings>'
            f'<extras />'
            f'<hashes />'
            f'<images>'
            f'<preview>{preview_data}</preview>'
            f'<icon>iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAARzQklUCAgICHwIZIgAAAMpSURBVGiB7ZdNSBRhGMd/M1NJhZaGlRHmIRULsmN0sGsXqUOnoEMQhF07WRB0SPuAkjBCSTzUIfDS0sEgsCw6lVQmmbrq+oHa5k7q6urqzkyHSXTdHZuvnF3Z32n2fR/m/f/3fd73eUZA04SydxxWFao1OAPkkdrIAvhEidruCvxCWbtWrCi8BEq9VmaRHkmiUlQVqkk/8QClqkK1UNKmhUj9tDFCFklf8QB5otcKnJIx4DUZA16zxWjidD5cL4a9WRspJ5FgFGr6oPVX8nnDHUgF8aBruFZsPG9oIBXEL7OelrQ/AxkDXuO6gZgG84rbbzXG8Bq1w6cpeDgIEQVO5MKVItghublCIq4ZGIrA1e8wEdV/d4Vh91a4VBgfp2owp0C2Syu7lkKd4RXxABrwdDQxbmQeqr7B2II767pmQEg2tmZQ0aBhGD5OwYMBWFKdr+uagWM5ULCq4AjAhYPxMa+C8GJCf34bgt455+s6NjC+AFEVCrdD3VE4mQvlOVBVBOcPrMT9ikJ9QN8FgJkYPArot5YTHB2l0QW4+AUuH4JzBXB8Fzwp10Vlrflrno9DIBI/9mYSWoNQuc++Bts7EFXhrh+G5/Vuse9vOkhCoviuMDQEYG3Kq0DjEPxesqvCgYGvM/Be1p/nFLjZC9NJhMzE4LYflgxSpT8Crw1aZTPYMjCvwL1+vWAt0zEFvp+JsW2T8Hna+F2KBnWDEFq0o8SGAQ1oGoHOmfhxFagbgI5VYscX4I7/3wc1tAj3B1YOuBUsGwhEoGUs+dycArf69JyOqnrqyCbzu20SematqrFhoGk4vuKu5UcYno3qKdUum3+vvASNw1bVWLhGNeCDDC3j68cpwOMhvahZ7Upbg3B2P5zak7yyJ8P0DszGoH7QXKyi6TXCDo1DEImZjze9AzsluFECIQd3thnyt1lrwU0bEAU4km1H0v8l80npNYYGgutclRvNeloMDdT0pYaJYFQvjkYIJW2aw47cWzbvGUgXMga8ZlMYsND0phyyKIDPaxV2EcAnihK1QI/XYmzQI0rUit0V+CWJSgGaSY90kgVoliQquyvw/wEBywt7TQ67XwAAAABJRU5ErkJggg==</icon>'
            f'</images>'
            f'<uris />'
            f'</content>'
            f'</message>'
        )

        packets = [data[s:s + 16384].encode() for s in range(0, len(data), 16384)]
        return list(packets)


class OutgoingGroupChatImage(OutgoingChatImage):
    """
    Represents an outgoing image chat message to a group
    """

    def __init__(self, group_jid, file_location):
        super().__init__(group_jid, file_location, is_group=True)


class IncomingChatMessage(XMPPResponse):
    """
    Represents an incoming text chat message from another user
    """

    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.request_delivered_receipt = data.request['d'] == 'true' if data.request else False
        self.request_read_receipt = data.request['r'] == 'true' if data.request else False
        self.status = data.status.text if data.status else None
        self.preview = data.preview.text if data.preview else None

        self.from_jid = data['from']
        self.to_jid = data['to']
        self.body = data.body.text if data.body else None
        self.is_typing = data.find('is-typing')
        self.is_typing = self.is_typing['val'] == 'true' if self.is_typing else None


class IncomingGroupChatMessage(IncomingChatMessage):
    """
    Represents an incoming text chat message from a group
    """

    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.group_jid = data.g['jid']
        # Messages from public groups include an alias user which can be resolved with client.xiphias_get_users_by_alias
        self.alias_sender = data.find('alias-sender').text if data.find('alias-sender') else None


class OutgoingReadReceipt(XMPPElement):
    """
    Represents an outgoing read receipt to a specific user, for one or more messages
    """

    def __init__(self, peer_jid, receipt_message_id, group_jid=None):
        super().__init__()
        self.peer_jid = peer_jid
        self.receipt_message_id = receipt_message_id
        self.group_jid = group_jid

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        group_line = "<g jid=\"{}\" />".format(self.group_jid)
        data = ('<message type="receipt" id="{}" to="{}" cts="{}">'
                '<kik push="false" qos="true" timestamp="{}" />'
                '<receipt xmlns="kik:message:receipt" type="read">'
                '<msgid id="{}" />'
                '</receipt>').format(self.message_id, self.peer_jid, timestamp, timestamp, self.receipt_message_id)
        if 'groups' in group_line:
            data = data + group_line + '</message>'
        else:
            data = data + '</message>'
        return data.encode()


class OutgoingDeliveredReceipt(XMPPElement):
    def __init__(self, peer_jid, receipt_message_id, group_jid=None):
        super().__init__()

        self.group_jid = group_jid
        self.peer_jid = peer_jid
        self.receipt_message_id = receipt_message_id

    def serialize(self):
        if self.group_jid and 'groups.kik.com' in self.group_jid:
            g_tag = " g=\"{}\"".format(self.group_jid)
        else:
            g_tag = ''

        timestamp = str(int(round(time.time() * 1000)))
        data = ('<iq type="set" id="{}" cts="{}">'
                '<query xmlns="kik:iq:QoS">'
                '<msg-acks>'
                '<sender jid="{}"{}>'
                '<ack-id receipt="true">{}</ack-id>'
                '</sender>'
                '</msg-acks>'
                '<history attach="false" />'
                '</query>'
                '</iq>').format(self.message_id, timestamp, self.peer_jid, g_tag, self.receipt_message_id)
        return data.encode()


class OutgoingIsTypingEvent(XMPPElement):
    def __init__(self, peer_jid, is_typing):
        super().__init__()
        self.peer_jid = peer_jid
        self.is_typing = is_typing

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        data = ('<message type="chat" to="{}" id="{}">'
                '<kik push="false" qos="false" timestamp="{}" />'
                '<is-typing val="{}" />'
                '</message>').format(self.peer_jid, self.message_id, timestamp, str(self.is_typing).lower())
        return data.encode()


class OutgoingGroupIsTypingEvent(XMPPElement):
    def __init__(self, group_jid, is_typing):
        super().__init__()
        self.peer_jid = group_jid
        self.is_typing = is_typing

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        data = ('<message type="groupchat" to="{}" id="{}">'
                '<pb></pb>'
                '<kik push="false" qos="false" timestamp="{}" />'
                '<is-typing val="{}" />'
                '</message>').format(self.peer_jid, self.message_id, timestamp, str(self.is_typing).lower())
        return data.encode()


class OutgoingLinkShareEvent(XMPPElement):
    def __init__(self, peer_jid, link, title, text, app_name, preview):
        super().__init__()
        self.peer_jid = peer_jid
        self.link = link
        self.title = title
        self.text = text
        self.app_name = app_name
        if not preview:
            self.preview = ''
        else:
            self.preview = self.get_preview(preview)

    def serialize(self):
        message_type = 'type="groupchat" xmlns="kik:groups"' if 'group' in self.peer_jid else 'type="chat"'
        timestamp = str(int(round(time.time() * 1000)))
        data = ('<message {0} to="{1}" id="{2}" cts="{3}">'
                '<pb></pb>'
                '<kik push="true" qos="true" timestamp="{3}" />'
                '<request xmlns="kik:message:receipt" r="true" d="true" />'
                '<content id="{2}" app-id="com.kik.cards" v="2">'
                '<strings>'
                '<app-name>{4}</app-name>'
                '<layout>article</layout>'
                '<title>{5}</title>'
                '<text>{6}</text>'
                '<allow-forward>true</allow-forward>'
                '</strings>'
                '<extras />'
                '<hashes />'
                '<images>'
                '<icon></icon>'
                '<preview>{8}</preview>'
                '</images>'
                '<uris>'
                '<uri platform="cards">{7}</uri>'
                '<uri></uri>'
                '<uri>http://cdn.kik.com/cards/unsupported.html</uri>'
                '</uris>'
                '</content>'
                '</message>').format(message_type, self.peer_jid, self.message_id, timestamp, self.app_name, self.title,
                                     self.text, self.link, self.preview)
        return data.encode()

    def get_preview(self, preview):
        img = Image.open(preview)
        buffered = BytesIO()
        img.convert("RGB").save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
        return img_str


class IncomingMessageReadEvent(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.receipt_message_id = data.receipt.msgid['id']
        self.from_jid = data['from']
        self.group_jid = data.g['jid'] if data.g else None


class IncomingMessageDeliveredEvent(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.receipt_message_id = data.receipt.msgid['id']
        self.from_jid = data['from']
        self.group_jid = data.g['jid'] if data.g else None


class IncomingIsTypingEvent(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.from_jid = data['from']
        self.is_typing = data.find('is-typing')['val'] == 'true'


class IncomingGroupIsTypingEvent(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.from_jid = data['from']
        self.is_typing = data.find('is-typing')['val'] == 'true'
        self.group_jid = data.g['jid']


class IncomingGroupStatus(XMPPResponse):
    """ xmlns=jabber:client type=groupchat """

    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.request_delivered_receipt = data.request['d'] == 'true' if data.request else False
        self.requets_read_receipt = data.request['r'] == 'true' if data.request else False
        self.group_jid = data['from']
        self.to_jid = data['to']
        self.status = data.status.text if data.status else None
        self.status_jid = data.status['jid'] if data.status and 'jid' in data.status.attrs else None
        self.group = Group(data.g) if data.g and len(data.g.contents) > 0 else None


class IncomingGroupSysmsg(XMPPResponse):
    """ xmlns=jabber:client type=groupchat """

    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.request_delivered_receipt = data.request['d'] == 'true' if data.request else False
        self.requets_read_receipt = data.request['r'] == 'true' if data.request else False
        self.group_jid = data['from']
        self.to_jid = data['to']
        self.sysmsg_xmlns = data.sysmsg['xmlns'] if data.sysmsg and 'xmlns' in data.sysmsg.attrs else None
        self.sysmsg = data.sysmsg.text if data.sysmsg else None
        self.group = Group(data.g) if data.g and len(data.g.contents) > 0 else None


class IncomingGroupReceiptsEvent(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        self.from_jid = data['from']
        self.to_jid = data['to']
        self.group_jid = data.g['jid']
        self.receipt_ids = [msgid['id'] for msgid in data.receipt.findAll('msgid')]
        self.type = data.receipt['type']


class IncomingFriendAttribution(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        friend_attribution = data.find('friend-attribution')
        self.context_type = friend_attribution.context['type']
        self.referrer_jid = friend_attribution.context['referrer']
        self.reply = friend_attribution.context['reply'] == 'true'
        self.body = friend_attribution.body.text


class IncomingStatusResponse(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        status = data.find('status')
        self.from_jid = data['from']
        self.status = status.text
        self.special_visibility = status['special-visibility'] == 'true'
        self.status_jid = status['jid']


class IncomingImageMessage(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        if data.request is not None:
            self.request_delivered_receipt = data.request['d'] == 'true'
        else:
            self.request_delivered_receipt = 'true'
        if data.request is not None:
            self.requets_read_receipt = data.request['r'] == 'true'
        else:
            self.requets_read_receipt = 'true'
        self.app_id = data.find('content').attrs["app-id"]
        self.app_name = data.find('app-name').get_text()
        self.spoof = False
        if self.app_id == "com.kik.ext.camera" and self.app_name == "Gallery":
            self.spoof = True
        self.image_url = data.find('file-url').get_text() if data.find('file-url') else None
        self.status = data.status.text if data.status else None
        self.from_jid = data['from']
        self.to_jid = data['to']
        self.group_jid = data.g['jid'] if data.g else None


class IncomingGroupSticker(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        content = data.content
        extras_map = self.parse_extras(content.extras)
        self.from_jid = data['from']
        self.group_jid = data.g['jid'] if data.g else None
        self.sticker_pack_id = extras_map['sticker_pack_id'] if 'sticker_pack_id' in extras_map else None
        self.sticker_url = extras_map['sticker_url'] if 'sticker_url' in extras_map else None
        self.sticker_id = extras_map['sticker_id'] if 'sticker_id' in extras_map else None
        self.sticker_source = extras_map['sticker_source'] if 'sticker_source' in extras_map else None
        self.png_preview = content.images.find('png-preview').text if content.images.find('png-preview') else None
        self.uris = []
        for uri in content.uris:
            self.uris.append(self.Uri(uri))

    class Uri:
        def __init__(self, uri):
            self.platform = uri['platform']
            self.url = uri.text

    @staticmethod
    def parse_extras(extras):
        extras_map = {}
        for item in extras.findAll('item'):
            extras_map[item.key.string] = item.val.text
        return extras_map


class IncomingGifMessage(XMPPResponse):
    """
    Represents an incoming GIF message from another kik entity, sent as a URL
    """

    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        if data.request is not None:
            self.request_delivered_receipt = data.request['d'] == 'true'
        else:
            self.request_delivered_receipt = 'true'
        if data.request is not None:
            self.requets_read_receipt = data.request['r'] == 'true'
        else:
            self.requets_read_receipt = 'true'
        self.status = data.status.text if data.status else None
        self.from_jid = data['from']
        self.to_jid = data['to']
        self.group_jid = data.g['jid'] if data.g else None
        if data.content.uris is not None:
            self.uris = [self.Uri(uri) for uri in data.content.uris]
        else:
            print("Missing URI")

    class Uri:
        def __init__(self, uri):
            # Because Navi doesn't send proper stanza for GIFs
            if uri.has_attr('file-content-type'):
                self.file_content_type = uri['file-content-type']
            else:
                self.file_content_type = "video/mp4"
            if uri.has_attr('type'):
                self.type = uri['type']
            else:
                self.type = uri['type'] = "video"
            self.url = uri.text


class OutgoingGIFMessage(XMPPElement):
    """
    Represents an outgoing GIF message to another kik entity (member or group)
    """

    def __init__(self, peer_jid, search_term, is_group=True):
        super().__init__()
        self.peer_jid = peer_jid
        self.allow_forward = True
        self.is_group = is_group
        self.gif_preview, self.gif_data = self.get_gif_data(search_term)

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        message_type = "chat" if not self.is_group else "groupchat"
        data = (
            '<message cts="{0}" type="{1}" to="{12}" id="{2}" xmlns="jabber:client">'
            '<kik push="true" timestamp="{3}" qos="true"/>'
            '<pb/>'
            '<content id="{4}" v="2" app-id="com.kik.ext.gif">'
            '<strings>'
            '<app-name>GIF</app-name>'
            '<layout>video</layout>'
            '<allow-forward>true</allow-forward>'
            '<disallow-save>true</disallow-save>'
            '<video-should-autoplay>true</video-should-autoplay>'
            '<video-should-loop>true</video-should-loop>'
            '<video-should-be-muted>true</video-should-be-muted>'
            '</strings>'
            '<images>'
            '<icon></icon>'
            '<preview>{5}</preview>'
            '</images>'
            '<uris>'
            '<uri priority="0" type="video" file-content-type="video/mp4">{6}</uri>'
            '<uri priority="1" type="video" file-content-type="video/webm">{7}</uri>'
            '<uri priority="0" type="video" file-content-type="video/tinymp4">{8}</uri>'
            '<uri priority="1" type="video" file-content-type="video/tinywebm">{9}</uri>'
            '<uri priority="0" type="video" file-content-type="video/nanomp4">{10}</uri>'
            '<uri priority="1" type="video" file-content-type="video/nanowebm">{11}</uri>'
            '</uris>'
            '</content>'
            '<request r="true" d="true" xmlns="kik:message:receipt"/>'
            '</message>'
        ).format(timestamp, message_type, self.message_id, timestamp, self.message_id, self.gif_preview,
                 self.gif_data["mp4"]["url"], self.gif_data["webm"]["url"], self.gif_data["tinymp4"]["url"],
                 self.gif_data["tinywebm"]["url"], self.gif_data["nanomp4"]["url"],
                 self.gif_data["nanowebm"]["url"], self.peer_jid)

        packets = [data[s:s + 16384].encode() for s in range(0, len(data), 16384)]
        return list(packets)

    def get_gif_data(self, search_term):
        apikey = "9IEG1MMRM3RY"  # add api key from https://tenor.com/gifapi
        if apikey == "":
            raise Exception("A tendor.com API key is required to search for GIFs images. please get one and change it")

        r = requests.get(f'https://api.tenor.com/v1/search?q={search_term}&key={apikey}&limit=10')
        if r.status_code == 200:
            gif = json.loads(r.content.decode())
            if len(gif["results"]) > 1:
                response_length = len(gif["results"])
                chosen_gif = random.randint(0, response_length)
            else:
                chosen_gif = 0
            response = requests.get(gif["results"][chosen_gif]["media"][0]["nanomp4"]["preview"])
            img = Image.open(BytesIO(response.content))
            buffered = BytesIO()

            img.convert("RGB").save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
            return img_str, gif["results"][chosen_gif]["media"][0]
        else:
            return ""


class OutgoingGIFMessageSub(XMPPElement):
    """
    Represents an outgoing GIF message sent via bot trigger
    """

    def __init__(self, peer_jid, gif_data_path, is_group=True):
        super().__init__()
        self.peer_jid = peer_jid
        self.allow_forward = True
        self.is_group = is_group
        self.gif_preview, self.gif_data = self.get_gif_data(gif_data_path)

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        message_type = "chat" if not self.is_group else "groupchat"
        data = (
            f'<message cts="{timestamp}" type="{message_type}" to="{self.peer_jid}" id="{self.message_id}" xmlns="jabber:client">'
            f'<kik push="true" timestamp="{timestamp}" qos="true"/>'
            f'<pb/>'
            f'<content id="{self.message_id}" v="2" app-id="com.kik.ext.gif">'
            f'<strings>'
            f'<app-name>GIF</app-name>'
            f'<layout>video</layout>'
            f'<allow-forward>true</allow-forward>'
            f'<disallow-save>true</disallow-save>'
            f'<video-should-autoplay>true</video-should-autoplay>'
            f'<video-should-loop>true</video-should-loop>'
            f'<video-should-be-muted>true</video-should-be-muted>'
            f'</strings>'
            f'<images>'
            f'<icon></icon>'
            f'<preview>{self.gif_preview}</preview>'
            f'</images>'
            f'<uris>'
            f'<uri priority="0" type="video" file-content-type="video/mp4">{self.gif_data["mp4"]}</uri>'
            f'<uri priority="1" type="video" file-content-type="video/webm">{self.gif_data["webm"]}</uri>'
            f'<uri priority="0" type="video" file-content-type="video/tinymp4">{self.gif_data["tinymp4"]}</uri>'
            f'<uri priority="1" type="video" file-content-type="video/tinywebm">{self.gif_data["tinywebm"]}</uri>'
            f'<uri priority="0" type="video" file-content-type="video/nanomp4">{self.gif_data["nanomp4"]}</uri>'
            f'<uri priority="1" type="video" file-content-type="video/nanowebm">{self.gif_data["nanowebm"]}</uri>'
            f'</uris>'
            f'</content>'
            f'<request r="true" d="true" xmlns="kik:message:receipt"/>'
            f'</message>'
        )
        packets = [data[s:s + 16384].encode() for s in range(0, len(data), 16384)]
        return list(packets)

    def get_gif_data(self, gif_path):
        with open(gif_path, 'r') as gif_file:
            content = json.load(gif_file)
        return content["preview"], content


class OutgoingCustomGIFMessage(XMPPElement):
    """
    Represents an outgoing custom GIF message to another kik entity (member or group)
    """

    def __init__(self, peer_jid, path, url, is_group=True):
        super().__init__()
        self.peer_jid = peer_jid
        self.allow_forward = True
        self.is_group = is_group
        self.gif_preview, self.gif_data = self.get_gif_data(path, url)

    def serialize(self):
        timestamp = str(int(round(time.time() * 1000)))
        message_type = "chat" if not self.is_group else "groupchat"
        data = (
            '<message cts="{0}" type="{1}" to="{12}" id="{2}" xmlns="jabber:client">'
            '<kik push="true" timestamp="{3}" qos="true"/>'
            '<pb/>'
            '<content id="{4}" v="2" app-id="com.kik.ext.gif">'
            '<strings>'
            '<app-name>GIF</app-name>'
            '<layout>video</layout>'
            '<allow-forward>true</allow-forward>'
            '<disallow-save>true</disallow-save>'
            '<video-should-autoplay>true</video-should-autoplay>'
            '<video-should-loop>true</video-should-loop>'
            '<video-should-be-muted>true</video-should-be-muted>'
            '</strings>'
            '<images>'
            '<icon></icon>'
            '<preview>{5}</preview>'
            '</images>'
            '<uris>'
            '<uri priority="0" type="video" file-content-type="video/mp4">{6}</uri>'
            '<uri priority="1" type="video" file-content-type="video/webm">{7}</uri>'
            '<uri priority="0" type="video" file-content-type="video/tinymp4">{8}</uri>'
            '<uri priority="1" type="video" file-content-type="video/tinywebm">{9}</uri>'
            '<uri priority="0" type="video" file-content-type="video/nanomp4">{10}</uri>'
            '<uri priority="1" type="video" file-content-type="video/nanowebm">{11}</uri>'
            '</uris>'
            '</content>'
            '<request r="true" d="true" xmlns="kik:message:receipt"/>'
            '</message>'
        ).format(timestamp, message_type, self.message_id, timestamp, self.message_id, self.gif_preview,
                 self.gif_data["mp4"]["url"], self.gif_data["webm"]["url"], self.gif_data["tinymp4"]["url"],
                 self.gif_data["tinywebm"]["url"], self.gif_data["nanomp4"]["url"],
                 self.gif_data["nanowebm"]["url"], self.peer_jid)

        packets = [data[s:s + 16384].encode() for s in range(0, len(data), 16384)]
        return list(packets)

    def get_gif_data(self, path, url):
        img = Image.open(path)
        buffered = BytesIO()
        img.convert("RGB").save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
        gif = {'mp4': {'url': url + '.mp4'}, 'webm': {'url': url + '.webm'}, 'tinymp4': {'url': url + '.mp4'},
               'tinywebm': {'url': url + '.webm'}, 'nanomp4': {'url': url + '.mp4'}, 'nanowebm': {'url': url + '.webm'}}

        return img_str, gif


class IncomingVideoMessage(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        if data.request is not None:
            self.request_delivered_receipt = data.request['d'] == 'true'
        else:
            self.request_delivered_receipt = 'true'
        if data.request is not None:
            self.requets_read_receipt = data.request['r'] == 'true'
        else:
            self.requets_read_receipt = 'true'
        self.app_id = data.find('content').attrs["app-id"]
        self.app_name = data.find('app-name').get_text()
        self.spoof = False
        if self.app_id == "com.kik.ext.camera" and self.app_name == "Gallery":
            self.spoof = True
        self.video_url = data.find('file-url').text
        self.file_content_type = data.find('file-content-type').text if data.find('file-content-type') else None
        self.duration_milliseconds = data.find('duration').text if data.find('duration') else None
        self.file_size = data.find('file-size').text
        self.from_jid = data['from']
        self.to_jid = data['to']
        self.group_jid = data.g['jid'] if data.g else None


class IncomingCardMessage(XMPPResponse):
    def __init__(self, data: BeautifulSoup):
        super().__init__(data)
        if data.request is not None:
            self.request_delivered_receipt = data.request['d'] == 'true'
        else:
            self.request_delivered_receipt = 'true'
        if data.request is not None:
            self.requets_read_receipt = data.request['r'] == 'true'
        else:
            self.requets_read_receipt = 'true'
        self.from_jid = data['from']
        self.to_jid = data['to']
        self.group_jid = data.g['jid'] if data.g else None
        self.app_name = data.find('app-name').text if data.find('app-name') else None
        self.card_icon = data.find('card-icon').text if data.find('card-icon') else None
        self.layout = data.find('layout').text if data.find('layout') else None
        self.title = data.find('title').text if data.find('title') else None
        self.text = data.find('text').text if data.find('text') else None
        self.allow_forward = data.find('allow-forward').text if data.find('allow-forward') else None
        self.icon = data.find('icon').text if data.find('icon') else None
        self.uri = data.find('uri').text if data.find('uri') else None
