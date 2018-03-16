#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import logging
import os

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


@app.route('/switch', methods=['GET'])
def switch():
    username = request.args.get('user_name')
    token = request.args.get('token')
    action = request.args.get('text')
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
    if app.config.get('GITHUB_WEBHOOK_TOKEN'):
        # Check validity of the webhook
        valid_signature = hmac.new(app.config['GITHUB_WEBHOOK_TOKEN'], request.data, hashlib.sha1).hexdigest()
        given_signature = request.headers.get('X-Hub-Signature', '').split('=')[-1]
        if not hmac.compare_digest(valid_signature, given_signature):
            abort(401)
    event_type = request.headers.get('X-GitHub-Event')
    to_notify, message = GithubHandler(event_type, request.get_json()).handle()
    emails = [app.config['EMAILS'][username] for username in to_notify if username in app.config['EMAILS']]
    logging.info((message, emails))
    if emails and message:
        slack.post_msg_to_users(message, emails=emails)
    return 'OK'


def run_server(host, port):
    app.run(host=host, port=port)
