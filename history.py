import re
from yarl import URL
from github import Github, GithubException
from discord import Embed

from logging import getLogger
logger = getLogger(__name__)


github_client = Github()
git_repo_regex = re.compile(
    'https://github.com/'
    '(?P<user>[0-9a-zA-Z-]+)/'    # User name
    '(?P<repo>[0-9a-zA-Z-]+)/'    # Repo name
    'blob/'
    '(?P<branch>[0-9a-zA-Z-]+)/'  # Branch name
    '(?P<filepath>.*)'            # File path
)


def _get_gist_ids(url: URL):
    for p in url.parts:
        if re.match(r'[0-9a-z]{32,}', p):
            yield p


def _get_gist_history(url: URL):
    try:
        ids = list(_get_gist_ids(url))
        if len(ids) > 1 or len(ids) == 0:
            # The first id is a gist id.
            # The second id is a gist revision sha.
            # if the URL has a second id, abort processing.
            return None
        id = ids[0]
        gist = github_client.get_gist(id)
    except GithubException:
        return None

    versions = [(h.version[0:5], f'https://gist.github.com/{h.id}/{h.version}')
                for h in gist.history]
    url = f'https://gist.github.com/{id}/{gist.history[0].version}'

    em = Embed(title=f'GitHub Gist',
               description=f'[Link for **HEAD**]({url})')
    em.set_author(name=gist.owner.login, url=gist.owner.html_url,
                  icon_url=gist.owner.avatar_url)
    em.add_field(name='revisions(latest 5)',
                 value='\n'.join(f'[{v[0]}]({v[1]})' for v in versions))
    em.set_footer(text=f'HEAD updated at:')
    em.timestamp = gist.updated_at
    return em


def _get_github_repo_history(url):
    match = git_repo_regex.match(str(url))

    if not match:
        return None

    repo = github_client.get_repo(f'{match["user"]}/{match["repo"]}')
    branches = list(repo.get_branches())
    checked_out = [b for b in branches if b.name == match['branch']][0].commit
    commits = repo.get_commits(sha=checked_out.sha)
    url = (f'https://github.com/{match["user"]}/{match["repo"]}'
           f'/blob/{checked_out.commit.sha}/{match["filepath"]}')

    em = Embed(title=f'GitHub Repository: {match["user"]}/{match["repo"]}',
               description=f'[Link for **HEAD**]({url})')
    em.set_author(name=repo.owner.login, url=repo.owner.html_url,
                  icon_url=repo.owner.avatar_url)
    em.add_field(
        name='branches',
        value='\n'.join(fr'\* **{b.name}**' if b.commit == checked_out else b.name
                        for b in branches))
    em.add_field(
        name='revisions(latest 5)',
        value='\n'.join(
            f'[{c.sha[:7]}]({c.html_url}): '
            f'{c.commit.message[:30]}{"..." if len(c.commit.message)>30 else ""}'
            for c in commits[:5]))
    em.set_footer(text=f'HEAD committed at:')
    em.timestamp = checked_out.commit.committer.date
    return em


def get_history(string):
    match = re.match(r'https?://[a-zA-Z0-9.%/-]+', string)
    if not match:
        logger.debug('No URL found in the message content')
        return

    url = URL(match[0])
    if url.host == 'gist.github.com':
        # GitHub Gist
        logger.info('GitHub Gist URL found in the message content')
        return _get_gist_history(url)

    elif git_repo_regex.match(str(url)):
        # GitHub Repository File
        logger.info('GitHub repo URL found in the message content')
        return _get_github_repo_history(url)

    else:
        logger.info('Found URL in the message content is not processable')
