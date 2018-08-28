# -*- coding: utf-8 -*-

import logging
import os
import time
import ujson as json

from slacker import Slacker

from . import app


logger = logging.getLogger(__name__)


class Slack(object):

    def __init__(self, auth_token, disable_list_file, username, avatar=None):
        self.client = Slacker(auth_token)
        self.email_name_map = {}
        self.email_name_map_updated = 0
        self.disable_list_file = disable_list_file
        self.username = username
        self.avatar = avatar

    def post_msg_to_users(self, msg=None, attachment=None, names=None, emails=None):
        self.check_refresh()
        names = names or []
        emails = emails or []
        for email in emails:
            name = self.email_name_map.get(email)
            if name:
                names.append(name)

        sent_names = []
        disabled_users = self.disabled_users
        for name in names:
            if name in disabled_users:
                continue
            params = dict(
                channel='@%s' % name,
                username=self.username,
            )
            if msg is not None:
                params['text'] = msg
            if attachment is not None:
                if self.avatar:
                    attachment['footer_icon'] = self.avatar
                params['attachments'] = json.dumps([attachment]),
            if self.avatar:
                params['icon_url'] = self.avatar
            self.client.chat.post_message(**params)
            sent_names.append(name)

        if names:
            logger.info('Message:\n\t %s\nhas been send to %r', msg, sent_names)

    def refresh_email_name_map(self):
        users = self.client.users.list().body['members']
        self.email_name_map = dict(
            [
                (user['profile'].get('email'), user['name'])
                for user in users
            ]
        )
        self.email_name_map_updated = time.time()

    def check_refresh(self):
        now = time.time()
        if now - self.email_name_map_updated >= app.config['SLACK_EMAIL_REFRESH_INTERVAL']:
            logging.info('Refreshing slack members.')
            self.refresh_email_name_map()

    def enable(self, name):
        disabled_users = self.disabled_users
        with open(self.disable_list_file, 'w+') as f:
            for n in disabled_users:
                if n != name:
                    f.write(n + '\n')

    def disable(self, name):
        if name not in self.disabled_users:
            with open(self.disable_list_file, 'a+') as f:
                f.write(name + '\n')

    @property
    def disabled_users(self):
        if not os.path.exists(self.disable_list_file):
            return []
        with open(self.disable_list_file, 'r') as disabled_users_file:
            return [line.strip() for line in disabled_users_file.readlines() if line.strip()]
