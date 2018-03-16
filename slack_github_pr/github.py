# -*- coding: utf-8 -*-
import logging


class GithubHandler(object):
    def __init__(self, payload):
        self.payload = payload
        self.action = self.payload.get('action')
        self.sender = self.payload.get('sender', {}).get('login')
        self.to_notify = []
        self.message = None

    def handle(self):
        if self.action == 'review_requested':
            self.handle_review_requested()
        return self.to_notify, self.message

    def handle_review_requested(self):
        pull_request = self.payload['pull_request']
        url = pull_request['html_url']
        self.to_notify = [reviewer['login'] for reviewer in pull_request['requested_reviewers']]
        self.message = "{} requested you to review PR #{}: {}".format(
            self.sender, pull_request['number'], pull_request['html_url'])
