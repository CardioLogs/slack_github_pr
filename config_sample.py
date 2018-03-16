# -*- coding: utf-8 -*-
GITHUB_WEBHOOK_TOKEN = 'github_webhook_token'

SLACK_AUTH_TOKEN = 'slack_auth_token'

SLACK_COMMAND_TOKEN = 'slack_command_token'

# Following settings are optional

# How often to refresh your slack member list (in seconds)?
SLACK_EMAIL_REFRESH_INTERVAL = 3600

# Pick a name to displayed in Slack of you notification bot
SLACK_BOT_NAME = 'GitHub'
SLACK_BOT_ICON = 'https://ca.slack-edge.com/T04KUQ181-U9PGT7AV9-09b2b129b8e1-48'

# Which file to record the disabled users?
DISABLED_USERS_FILE = './disabled_users.txt'

EMAILS = {
    'username': 'username@example.com',
}
