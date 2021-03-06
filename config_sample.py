# -*- coding: utf-8 -*-
SLACK_AUTH_TOKEN = 'slack_auth_token'

SLACK_COMMAND_TOKEN = 'slack_command_token'

# Following settings are optional

GITHUB_API_TOKEN = 'github_api_token'

GITHUB_WEBHOOK_TOKEN = b'github_webhook_token'

# How often to refresh your slack member list (in seconds)?
SLACK_EMAIL_REFRESH_INTERVAL = 3600

# Pick a name to displayed in Slack of you notification bot
SLACK_BOT_NAME = 'GitHub'
SLACK_BOT_ICON = 'https://ca.slack-edge.com/T04KUQ181-U9PGT7AV9-09b2b129b8e1-48'

# Which file to record the disabled users?
DISABLED_USERS_FILE = './disabled_users.txt'

# Ignore the following GitHub usernames when they perform actions (useful for bot accounts)
GITHUB_IGNORED_USERS = []

# Mapping between GitHub usernames and user's email address used on Slack
EMAILS = {
    'username': 'username@example.com',
}
