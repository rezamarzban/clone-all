#!/usr/bin/env python
"""
Clone all public and private repositories from a GitHub user or organization.

Copyright (c) 2018 Yuriy Guts

usage: github-clone-all.py [-h] [--auth-user AUTH_USER]
                           [--auth-password AUTH_PASSWORD] [--clone-user USER]
                           [--clone-org ORG]

optional arguments:
  -h, --help                      show this help message and exit
  --auth-user AUTH_USER           User for GitHub authentication.
  --auth-password AUTH_PASSWORD   Password or command line token for GitHub authentication.
  --clone-user USER               Which user's repos to clone.
  --clone-org ORG                 Which organization's repos to clone.
"""

from __future__ import division, print_function

import argparse
import os
import requests
import subprocess
import sys
import traceback


class HelpOnFailArgumentParser(argparse.ArgumentParser):
    """
    Prints help whenever the command-line arguments could not be parsed.
    """

    def error(self, message):
        sys.stderr.write('error: %s\n\n' % message)
        self.print_help()
        sys.exit(2)


class RepoEnumerationException(Exception):
    pass


def parse_command_line_args(args):
    """
    Parse command-line arguments and organize them into a single structured object.
    """

    program_desc = 'Clone all public and private repositories from a GitHub user or organization.'
    parser = HelpOnFailArgumentParser(description=program_desc)

    parser.add_argument('--auth-user', help='User for GitHub authentication.', required=False)
    parser.add_argument('--auth-password', help='Password or command line token for GitHub authentication.', required=False)
    parser.add_argument('--clone-user', metavar='USER', help="Which user's repos to clone.", required=False)
    parser.add_argument('--clone-org', metavar='ORG', help="Which organization's repos to clone.", required=False)

    # Try parsing the arguments and fail properly if that didn't succeed.
    parsed_args = parser.parse_args(args)
    if not parsed_args.clone_user and not parsed_args.clone_org:
        parser.print_help()
        sys.exit(2)

    if parsed_args.clone_user and parsed_args.clone_org:
        sys.stderr.write('error: cannot set clone-user and clone-org at the same time')
        parser.print_help()
        sys.exit(2)

    return parsed_args


def fetch_url(url, auth_user, auth_password):
    print('> HTTP fetch:', url)
    auth = requests.auth.HTTPBasicAuth(auth_user, auth_password) if auth_user or auth_password else None
    response = requests.get(url, auth=auth)
    return response


def parse_link_header(header_str):
    # Input: `<url&page=1>; rel="prev", <url&page=3>; rel="next"`
    # Result: {'prev': 'url&page=1', 'next': 'url&page=3'}
    result = {}
    links = [link.strip() for link in header_str.split(',')]

    for link in links:
        components = [component.strip('') for component in link.split(';')]
        url = components[0].strip('<>')
        rel = components[1].replace('rel=', '').strip(' "')
        result[rel] = url

    return result


def fetch_paginated_json(url, auth_user, auth_password):
    result = []
    current_page_url = url
    while current_page_url:
        response = fetch_url(current_page_url, auth_user, auth_password)
        result.extend(response.json())

        # There's only one page.
        if not 'Link' in response.headers:
            break

        # There might be more pages to retrieve.
        link_str = response.headers['Link']
        links = parse_link_header(link_str)
        current_page_url = links.get('next')

    return result


def get_command_output(command):
    print('> Running:', command)
    return subprocess.check_output(command, shell=True).decode('utf-8')


def is_repo_already_cloned(repo_name):
    return os.path.exists(repo_name) and os.path.exists(os.path.join(repo_name, '.git'))


def clone_repo(repo):
    """
    Clone and check out branches for a single repo.
    """
    repo_name = repo['name']
    repo_url = repo['html_url']

    # Clone the repo.
    print()
    print("-------- Cloning {} [{}] --------".format(repo_name, repo_url))

    if is_repo_already_cloned(repo_name):
        print('SKIP: repo already cloned')
        return

    get_command_output('git clone {}'.format(repo_url))

    # Get the name of the default branch.
    default_branch_name = get_command_output('cd {} && git rev-parse --abbrev-ref origin/HEAD'.format(repo_name))
    default_branch_name = default_branch_name.replace('origin/', '').rstrip() or 'master'

    print('Checking out default branch:', default_branch_name)
    get_command_output('cd {} && git checkout {} && git pull --all && git submodule update --init --recursive'.format(repo_name, default_branch_name))


def clone_all_repos(args):
    if args.clone_org:
        # Clone an organization.
        list_repos_url = 'https://api.github.com/orgs/{}/repos?per_page=100'.format(args.clone_org)
    else:
        # Clone a user.
        list_repos_url = 'https://api.github.com/users/{}/repos?per_page=100&type=all'.format(args.clone_user)
        # If the authenticated user owns the account, clone public and private repos owned by them.
        if args.auth_user and args.auth_user.lower() == args.clone_user.lower():
            list_repos_url = 'https://api.github.com/user/repos?per_page=100&type=owner'

    print('Querying GitHub API...')
    repos = fetch_paginated_json(list_repos_url, args.auth_user, args.auth_password)
    if not isinstance(repos, list):
        raise RepoEnumerationException(repos)

    # Print out all repos.
    print()
    print('Will clone the following repos:')
    for repo in repos:
        print('    * {}'.format(repo['name']))

    for repo in repos:
        try:
            clone_repo(repo)
        except Exception:
            print()
            print('ERROR while cloning a repo.')
            print()
            traceback.print_exc()


def main():
    parsed_args = parse_command_line_args(sys.argv[1:])

    try:
        clone_all_repos(parsed_args)
    except RepoEnumerationException as e:
        print('ERROR enumerating the repos (an incorrect GitHub username/password?).')
        print('GitHub response:', e)
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
