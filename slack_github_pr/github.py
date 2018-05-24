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
        self.object_type = 'PR' if 'pull_request' in self.issue else 'issue'
        self.users = []
        self.message = None

        if self.pull_request:
            self.object_type = 'PR'
            self.object = self.pull_request
        elif self.issue:
            self.object_type = 'issue'
            self.object = self.issue

    def build_message(self, action_desc):
        self.message = "{} {} {} {}#{}: {}. {}".format(
            self.sender, action_desc, self.object_type, self.payload['repository']['name'],
            self.object['number'], self.object['title'], self.object['html_url'])

    def handle(self):
        if self.object is None or self.sender in app.config['GITHUB_IGNORED_USERS']:
            # Ignore the current action
            return [], ""
        if self.action == 'review_requested':
            self.handle_review_requested()
        elif self.event_type == 'pull_request_review' and self.action == 'submitted':
            self.handle_review_submitted()
        elif self.action == 'synchronize':
            self.handle_object_update('updated')
        elif self.event_type == 'pull_request' and self.action == 'closed':
            self.handle_object_update('closed')
        elif self.event_type == 'issues' and self.action == 'closed':
            self.handle_object_update('closed')
        elif self.action == 'assigned':
            self.handle_assigned()
        elif self.event_type == 'issue_comment' and self.action == 'created':
            self.handle_object_update('commented on')
        to_notify = set(user['login'] for user in self.users if user['login'] != self.sender)
        return to_notify, self.message

    def handle_review_requested(self):
        self.users = [self.payload['requested_reviewer']]
        self.build_message('requested you to review')

    def handle_assigned(self):
        self.users = [self.payload['assignee']]
        self.build_message('assigned to you')

    def handle_object_update(self, action_desc):
        self.users = [self.object['user']]
        self.users += self.object.get('requested_reviewers', [])
        self.users += self.object.get('assignees', [])
        self.build_message(action_desc)

    def handle_review_submitted(self):
        state = self.payload['review']['state']
        if state == "commented":
            action_desc = "commented on"
        elif state == "changes_requested":
            action_desc = "requested changes on"
        else:
            action_desc = "approved"
        self.handle_object_update(action_desc)
