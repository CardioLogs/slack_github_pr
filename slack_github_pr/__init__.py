# -*- coding: utf-8 -*-

import logging
import sys

from flask import Flask

app = Flask(__name__)

# configure log
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

from slack_github_pr import github
from slack_github_pr import slack
from slack_github_pr import web


__all__ = [
    'app',
    'github',
    'slack',
    'web',
]
