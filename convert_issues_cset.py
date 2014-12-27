# -*- coding: utf-8 -*-

import json
import sys
import re


class NodeToHash(object):

    def __init__(self, hg_logs, git_logs):
        self.hg_to_git = {}
        date_to_hg = {}

        for hg_log in hg_logs:
            node = hg_log['node'].strip()
            date_to_hg[hg_log['date'].strip()] = node
            self.hg_to_git[node] = None

        for git_log in git_logs:
            date = git_log['date'].strip()
            if date not in date_to_hg:
                #print('%r is not found in hg log' % git_log)
                continue
            self.hg_to_git[date_to_hg[date]] = git_log['node'].strip()

    def __call__(self, hg_node):
        if hg_node not in self.hg_to_git:
            print('%r is not found in hg log' % hg_node)
            return '?'

        return self.hg_to_git[hg_node]


def update_cset(content, node_to_hash):
    r"""
    replace '<<cset 0f18c81b53fc>>' pattern in content.

    before: '<<cset 0f18c81b53fc>>'  (hg-node)
    after: '\<\<cset 20fa9c09b23e\>\>'  (git-hash)
    """
    hg_nodes = re.findall(r'<<cset ([^>]+)>>', content)
    for hg_node in hg_nodes:
        git_hash = node_to_hash(hg_node)
        content = content.replace(r'<<cset %s>>' % hg_node, r'\<\<cset %s\>\>' % git_hash)
    return content


def convert_issues_cset(infile, outfile, hglogfile, gitlogfile):
    with open(hglogfile) as f:
        hglogs = json.load(f)['messages']
    with open(gitlogfile) as f:
        gitlogs = json.load(f)['messages']
    with open(infile) as f:
        issues = json.load(f)

    node_to_hash = NodeToHash(hglogs, gitlogs)

    for issue in issues['issues']:
        issue['issue']['content'] = update_cset(issue['issue']['content'], node_to_hash)
        for comment in issue['comments']:
            comment['body'] = update_cset(comment['body'], node_to_hash)

    with open(outfile, 'w') as f:
        json.dump(issues, f, indent=4)


if __name__ == '__main__':
    try:
        infile, outfile, hglogfile, gitlogfile = sys.argv[1:5]
    except (ValueError, IndexError):
        print('Usage:\n  {} input.json output.json hglog.json gitlog.json'.format(sys.argv[0]))
        sys.exit(-1)

    convert_issues_cset(infile, outfile, hglogfile, gitlogfile)