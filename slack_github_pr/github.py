# -*- coding: utf-8 -*-
import logging
import re
import requests

from . import app


# Regex from https://github.com/shinnn/github-username-regex
USERNAME_RE = re.compile(r"@[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}", re.I)


class GithubHandler(object):
    def __init__(self, event_type, payload):
        self.event_type = event_type
        self.payload = payload
        self.action = self.payload.get('action')
        self.sender = self.payload.get('sender', {})
        self.sender_name = self.sender.get('login')
        self.issue = self.payload.get('issue', {})
        self.pull_request = self.payload.get('pull_request', {})
        self.comment = self.payload.get('comment', {})
        self.object_type = 'PR' if 'pull_request' in self.issue else 'issue'
        self.users = []
        self.message = None
        self.mentioned_users = []

        if self.pull_request:
            self.object_type = 'PR'
            self.object = self.pull_request
        elif self.issue:
            self.object_type = 'Issue'
            self.object = self.issue

    def api_request(self, url):
        response = requests.get(
            url,
            headers={'Authorization': 'token {}'.format(app.config['GITHUB_API_TOKEN'])}
        )
        return response.json() if response.status_code == 200 else None

    def get_all_reviewers(self):
        reviewers = self.object.get('requested_reviewers', [])
        if self.object_type == 'PR':
            reviews = self.api_request(self.object['_links']['self']['href'] + '/reviews')
            if reviews is not None:
                reviewers += [review['user'] for review in reviews]
        return reviewers

    def is_pr_update_relevant(self):
        """Returns False if the PR update is just a merge"""
        before = self.payload.get('before')
        after = self.payload.get('after')
        base_branch = self.pull_request['base']['ref']
        url = self.payload['repository']['compare_url'].format(base=before, head=after)
        compare = self.api_request(url)
        if compare is None or compare['behind_by'] > 0 or compare['total_commits'] == 0:
            return True
        merge_commit_name = "Merge branch '{}'".format(base_branch)
        return not compare['commits'][-1]['commit']['message'].startswith(merge_commit_name)

    def build_message(self, action_desc):
        action_str = "{} {}".format(self.sender_name, action_desc)
        title = "{} #{} {}".format(self.object_type, self.object['number'], self.object['title'])
        fallback = "{} {}".format(action_str, title)
        repo = self.payload.get('repository', {})
        footer = "<{}|{}>".format(repo.get('html_url'), repo.get('full_name'))
        color = '#00b541'
        if self.object.get('merged'):
            color = '#8200c4'
        elif self.object.get('state') == 'closed':
            color = '#d6002b'
        self.message = {
            "fallback": fallback,
            "color": color,
            "author_name": action_str,
            "author_icon": self.sender.get('avatar_url'),
            "title": title,
            "title_link": self.object['html_url'],
            "footer": footer,
        }

    def handle(self):
        if self.object is None or self.sender_name in app.config['GITHUB_IGNORED_USERS']:
            # Ignore the current action
            return []
        if self.action == 'review_requested':
            self.handle_review_requested()
        elif self.event_type == 'pull_request_review' and self.action == 'submitted':
            self.handle_review_submitted()
        elif self.action == 'synchronize':
            # Ignore 'merge' updates
            if self.is_pr_update_relevant():
                self.handle_object_update('updated')
        elif self.event_type == 'pull_request' and self.action == 'closed':
            self.handle_object_update('closed')
        elif self.event_type == 'issues' and self.action == 'opened':
            self.handle_mentions(self.issue)
        elif self.event_type == 'issues' and self.action == 'closed':
            self.handle_object_update('closed')
        elif self.action == 'assigned':
            self.handle_assigned()
        elif self.event_type == 'issue_comment' and self.action == 'created':
            self.handle_object_update('commented on')
            self.handle_mentions(self.comment)
        elif self.event_type == 'pull_request_review_comment' and self.action == 'created':
            self.handle_mentions(self.comment)
        to_notify = set(user['login'] for user in self.users if user['login'] != self.sender_name)
        notifications = [[to_notify, self.message]]
        if self.mentioned_users:
            notifications.append([self.mentioned_users, self.build_message('mentioned you in')])
        return notifications

    def handle_review_requested(self):
        self.users = [self.payload['requested_reviewer']]
        self.build_message('requested you to review')

    def handle_assigned(self):
        self.users = [self.payload['assignee']]
        self.build_message('assigned to you')

    def handle_object_update(self, action_desc):
        self.users = [self.object['user']]
        self.users += self.get_all_reviewers()
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
        self.handle_mentions(self.payload['review'])

    def handle_mentions(self, obj):
        if obj is not None:
            body = obj.get('body', '')
            if body:
                self.mentioned_users = set(
                    username[1:] for username in USERNAME_RE.findall(body)
                    if username[1:] != self.sender_name
                )
