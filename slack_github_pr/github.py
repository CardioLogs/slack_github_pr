# -*- coding: utf-8 -*-
import logging

from . import app


class GithubHandler(object):
    def __init__(self, event_type, payload):
        self.event_type = event_type
        self.payload = payload
        self.action = self.payload.get('action')
        self.sender = self.payload.get('sender', {}).get('login')
        self.issue = self.payload.get('issue', {})
        self.pull_request = self.payload.get('pull_request', {})
        self.users = []
        self.message = None

    def handle(self):
        if self.sender in app.config['GITHUB_IGNORED_USERS']:
            # Ignore the current action
            return [], ""
        if self.action == 'review_requested':
            self.handle_review_requested()
        elif self.event_type == 'pull_request_review' and self.action == 'submitted':
            self.handle_review_submitted()
        elif self.action == 'synchronize':
            self.handle_pull_request_update('updated')
        elif self.event_type == 'pull_request' and self.action == 'closed':
            self.handle_pull_request_update('closed')
        elif self.event_type == 'issues' and self.action == 'closed':
            self.handle_issue_update('closed')
        elif self.event_type == 'issues' and self.action == 'assigned':
            self.handle_issue_assigned()
        elif self.event_type == 'issue_comment' and self.action == 'created':
            self.handle_issue_update('commented on')
        to_notify = set(user['login'] for user in self.users if user['login'] != self.sender)
        return to_notify, self.message

    def handle_review_requested(self):
        self.users = [self.payload['requested_reviewer']]
        self.message = "{} requested you to review PR #{}: {}. {}".format(
            self.sender, self.pull_request['number'], self.pull_request['title'],
            self.pull_request['html_url'])

    def handle_review_submitted(self):
        state = self.payload['review']['state']
        if state == "commented":
            result = "commented on"
        elif state == "changes_requested":
            result = "requested changes on"
        else:
            result = "approved"
        self.users = self.pull_request['requested_reviewers'] + [self.pull_request['user']]
        self.message = "{} {} PR #{}: {}. {}".format(
            self.sender, result, self.pull_request['number'], self.pull_request['title'],
            self.pull_request['html_url'])

    def handle_pull_request_update(self, update_type):
        self.users = self.pull_request['requested_reviewers'] + [self.pull_request['user']]
        self.message = "{} {} PR #{}: {}. {}".format(
            self.sender, update_type, self.pull_request['number'],
            self.pull_request['title'], self.pull_request['html_url'])

    def handle_issue_assigned(self):
        self.users = [self.payload['assignee']]
        self.message = "{} assigned to you issue #{}: {}. {}".format(
            self.sender, self.issue['number'], self.issue['title'], self.issue['html_url'])

    def handle_issue_update(self, update_type):
        object_type = 'PR' if 'pull_request' in self.issue else 'issue'
        self.users = self.issue['assignees'] + [self.issue['user']]
        self.message = "{} {} {} #{}: {}. {}".format(
            self.sender, update_type, object_type, self.issue['number'],
            self.issue['title'], self.issue['html_url'])
