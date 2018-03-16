#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time
import ujson as json

from flask import request, abort

from .github import GithubHandler
from .slack import Slack
from . import app


# load settings
app.config.from_pyfile(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.py'))
)

slack = Slack(
    auth_token=app.config['SLACK_AUTH_TOKEN'],
    disable_list_file=app.config['DISABLED_USERS_FILE'],
    username=app.config['SLACK_BOT_NAME'],
    avatar=app.config.get('SLACK_BOT_ICON'),
)


@app.route('/switch', methods=['POST'])
def switch():
    username = request.form.get('user_name')
    token = request.form.get('token')
    action = request.form.get('text')
    if not action or action not in ['disable', 'enable']:
        action = 'enable'
    action = action.strip()

    if token != app.config['SLACK_COMMAND_TOKEN']:
        abort(403)

    if action == 'enable':
        slack.enable(username)
    elif action == 'disable':
        slack.disable(username)
    else:
        abort(401)
    return '%s success.' % action


@app.route('/github-webhook', methods=['POST'])
def handle_webhook():
    payload = json.loads(request.get_json())
    #if payload.get('hook', {}).get('config', {}).get('secret') != app.config['GITHUB_WEBHOOK_TOKEN']:
    #    abort(401)
    to_notify, message = GithubHandler(payload).handle()
    to_notify = ['pomier']
    emails = [app.config['EMAILS'][username] for username in to_notify if username in app.config['EMAILS']]
    logging.info((message, emails))
    slack.post_msg_to_users(message, emails=emails)
    return 'OK'


def run_server(host, port):
    app.run(host=host, port=port)
