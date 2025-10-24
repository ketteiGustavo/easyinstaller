from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from easyinstaller.i18n.i18n import _

console = Console()

app = typer.Typer(
    name='changelog',
    help=_('Shows recent commits grouped by conventional commit type.'),
    invoke_without_command=True,
)

FORMAT_CHOICES = ('text', 'md', 'raw')
MAIN_TYPES = ('feat', 'fix', 'docs')
OTHER_TYPES = ('refactor', 'test', 'build', 'ci', 'style', 'chore', 'perf')
TYPE_LABELS: Dict[str, str] = {
    'feat': '✨ Features',
    'fix': '🐞 Bug Fixes',
    'docs': '📚 Documentation',
    'chore': '🧹 Chores',
    'refactor': '🔨 Refactoring',
    'test': '🧪 Tests',
    'build': '🏗 Build',
    'ci': '🔁 CI',
    'style': '🎨 Style',
    'perf': '⚡ Performance',
    'other': '📦 Other',
}

COMMIT_RE = re.compile(
    r'^(?::[^:]+:\s*)*(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:\s+(?P<subject>.+)'
)
REVERT_RE = re.compile(r'[Rr]everts?\s+commit\s+([0-9a-f]{7,40})')


class GitError(RuntimeError):
    """Raised when a git command cannot be completed."""


@dataclass
class CommitEntry:
    type: str
    scope: str
    subject: str
    commit_hash: str
    breaking: bool = False


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ['git', *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        raise GitError(stderr or stdout or 'git command failed')
    return result.stdout.strip()


def _ensure_git_repository() -> Optional[str]:
    try:
        return _run_git('rev-parse', '--show-toplevel')
    except GitError:
        return None


def _latest_tag(ref: str = 'HEAD') -> Optional[str]:
    try:
        return _run_git('describe', '--tags', '--abbrev=0', ref)
    except GitError:
        return None


def _previous_tag(tag: str) -> Optional[str]:
    try:
        return _run_git('describe', '--tags', '--abbrev=0', f'{tag}^')
    except GitError:
        return None


def _root_commit() -> Optional[str]:
    try:
        roots = _run_git('rev-list', '--max-parents=0', 'HEAD')
    except GitError:
        return None
    return roots.splitlines()[0] if roots else None


def _repo_remote_url() -> Optional[str]:
    try:
        url = _run_git('remote', 'get-url', 'origin')
    except GitError:
        return None
    return url[:-4] if url.endswith('.git') else url


def _candidate_changelog_paths() -> List[Path]:
    candidates: List[Path] = []

    # Current working directory
    candidates.append(Path.cwd() / 'CHANGELOG.md')

    # Relative to this module (source tree scenario)
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        candidates.append(parent / 'CHANGELOG.md')

    # Relative to the executable (frozen binary scenario)
    exe_path = Path(sys.executable).resolve()
    candidates.append(exe_path.parent / 'CHANGELOG.md')
    candidates.append(exe_path.parent.parent / 'CHANGELOG.md')

    seen: set[Path] = set()
    ordered: List[Path] = []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _locate_changelog_file() -> Optional[Path]:
    for path in _candidate_changelog_paths():
        if path.is_file():
            return path
    return None


def _render_changelog_file(fmt: str, options_used: bool = False) -> None:
    changelog_path = _locate_changelog_file()

    if changelog_path is None:
        console.print(
            _(
                '[red]Error:[/red] Unable to locate a CHANGELOG.md file. Run this command inside the project repository or download the release assets.'
            )
        )
        raise typer.Exit(1)

    console.print(
        _('[yellow]No Git repository detected. Showing CHANGELOG.md contents instead.[/yellow]')
    )
    if options_used:
        console.print(
            _('[yellow]Warning:[/yellow] Git-specific options were ignored while reading the bundled changelog.')
        )

    content = changelog_path.read_text(encoding='utf-8')
    if fmt == 'text':
        console.print(Markdown(content))
    else:
        typer.echo(content)


def _collect_commits(revision: str) -> List[CommitEntry]:
    log_format = '%H%x1f%s%x1f%b%x1e'
    try:
        raw_log = _run_git(
            'log',
            revision,
            '--no-merges',
            f'--pretty=format:{log_format}',
        )
    except GitError:
        return []

    commits: List[CommitEntry] = []
    reverted_prefixes: List[str] = []

    for entry in raw_log.split('\x1e'):
        if not entry.strip():
            continue
        parts = entry.split('\x1f')
        if len(parts) < 3:
            continue
        commit_hash, subject, body = parts[0], parts[1], parts[2]

        revert_match = REVERT_RE.search(body) if subject.startswith('Revert') else None
        if revert_match:
            reverted_prefixes.append(revert_match.group(1))
            continue

        if any(commit_hash.startswith(prefix) for prefix in reverted_prefixes):
            continue

        match = COMMIT_RE.match(subject)
        if match:
            commit_type = match.group('type').lower()
            scope = match.group('scope') or ''
            subject_text = match.group('subject').strip()
            is_breaking = bool(match.group('breaking'))
        else:
            commit_type = 'other'
            scope = ''
            subject_text = subject.strip()
            is_breaking = False

        if 'BREAKING CHANGE:' in body:
            is_breaking = True

        if commit_type not in MAIN_TYPES + OTHER_TYPES:
            commit_type = 'other'

        commits.append(
            CommitEntry(
                type=commit_type,
                scope=scope,
                subject=subject_text,
                commit_hash=commit_hash,
                breaking=is_breaking,
            )
        )

    return commits


def _group_commits(
    commits: Iterable[CommitEntry],
) -> tuple[Dict[str, List[CommitEntry]], List[CommitEntry]]:
    sections: Dict[str, List[CommitEntry]] = defaultdict(list)
    breakings: List[CommitEntry] = []
    for commit in commits:
        if commit.breaking:
            breakings.append(commit)
        sections[commit.type].append(commit)
    return sections, breakings


def _format_header(level: int, title: str, fmt: str) -> str:
    if fmt == 'md':
        return f"{'#' * level} {title}\n"
    if fmt == 'raw':
        underline = '-' * len(title)
        return f'{title}\n{underline}\n'
    return f'[bold]{title}[/bold]'


def _format_entry(commit: CommitEntry, fmt: str, repo_url: Optional[str]) -> str:
    scope_part = f'[{commit.scope}] ' if commit.scope else ''
    short_hash = commit.commit_hash[:7]
    if fmt == 'md':
        if repo_url:
            return f'- {scope_part}{commit.subject} ([`{short_hash}`]({repo_url}/commit/{commit.commit_hash}))\n'
        return f'- {scope_part}{commit.subject} (`{short_hash}`)\n'
    if fmt == 'raw':
        return f'- {scope_part}{commit.subject} ({short_hash})'
    return f'- {scope_part}{commit.subject} [dim]({short_hash})[/dim]'


def _render_text(
    sections: Dict[str, List[CommitEntry]],
    breakings: List[CommitEntry],
) -> None:
    console.print(_format_header(2, _('Changelog'), 'text'))
    console.print()

    if breakings:
        console.print(_format_header(3, '⚠ Breaking Changes', 'text'))
        for commit in breakings:
            console.print(_format_entry(commit, 'text', None))
        console.print()

    for commit_type in MAIN_TYPES:
        entries = sections.get(commit_type)
        if not entries:
            continue
        console.print(_format_header(3, TYPE_LABELS.get(commit_type, TYPE_LABELS['other']), 'text'))
        for commit in entries:
            console.print(_format_entry(commit, 'text', None))
        console.print()

    other_entries = []
    for commit_type in OTHER_TYPES:
        other_entries.extend(sections.get(commit_type, []))

    if other_entries:
        console.print(_format_header(3, TYPE_LABELS['other'], 'text'))
        for commit in other_entries:
            console.print(_format_entry(commit, 'text', None))


def _render_plain(
    sections: Dict[str, List[CommitEntry]],
    breakings: List[CommitEntry],
    fmt: str,
    repo_url: Optional[str],
) -> str:
    lines: List[str] = []
    lines.append(_format_header(2, _('Changelog'), fmt))

    if breakings:
        lines.append(_format_header(3, '⚠ Breaking Changes', fmt))
        for commit in breakings:
            lines.append(_format_entry(commit, fmt, repo_url).rstrip())
        lines.append('')

    for commit_type in MAIN_TYPES:
        entries = sections.get(commit_type)
        if not entries:
            continue
        lines.append(_format_header(3, TYPE_LABELS.get(commit_type, TYPE_LABELS['other']), fmt))
        for commit in entries:
            lines.append(_format_entry(commit, fmt, repo_url).rstrip())
        lines.append('')

    others_available = any(sections.get(t) for t in OTHER_TYPES)
    if others_available and fmt != 'md':
        lines.append(_format_header(3, TYPE_LABELS['other'], fmt))
    for commit_type in OTHER_TYPES:
        entries = sections.get(commit_type)
        if not entries:
            continue
        if fmt == 'md':
            lines.append(_format_header(3, TYPE_LABELS.get(commit_type, TYPE_LABELS['other']), fmt))
        for commit in entries:
            lines.append(_format_entry(commit, fmt, repo_url).rstrip())

    return '\n'.join(line for line in lines if line is not None).strip() + '\n'


@app.callback(invoke_without_command=True)
def changelog(
    ctx: typer.Context,
    fmt: str = typer.Option(
        'text',
        '--format',
        '-f',
        help=_('Output format: text (default), md, or raw.'),
        show_default=True,
    ),
    tag: Optional[str] = typer.Option(
        None,
        '--tag',
        help=_('Use a specific tag as the upper bound instead of the latest tag.'),
    ),
    since: Optional[str] = typer.Option(
        None,
        '--since',
        help=_('Optional starting reference for the changelog range.'),
    ),
    until: Optional[str] = typer.Option(
        None,
        '--until',
        help=_('Optional ending reference for the changelog range. Defaults to the provided tag or HEAD.'),
    ),
) -> None:
    """
    Shows recent commits grouped by conventional commit type. Defaults to the diff between the latest tag and the previous tag.
    """
    if ctx.invoked_subcommand is not None:
        return

    fmt = fmt.lower()

    if fmt not in FORMAT_CHOICES:
        console.print(
            _('[red]Error:[/red] Invalid format "{value}". Choose from: {choices}.').format(
                value=fmt, choices=', '.join(FORMAT_CHOICES)
            )
        )
        raise typer.Exit(1)

    repo_root = _ensure_git_repository()

    if repo_root is None:
        options_used = any([tag, since, until])
        _render_changelog_file(fmt, options_used=options_used)
        return

    upper_ref = until or tag or _latest_tag() or 'HEAD'
    lower_ref: Optional[str] = since

    if lower_ref is None:
        if tag or until:
            previous = _previous_tag(upper_ref)
            lower_ref = previous or _root_commit()
        else:
            latest_tag = _latest_tag()
            if latest_tag:
                previous_tag = _previous_tag(latest_tag)
                upper_ref = latest_tag
                lower_ref = previous_tag or _root_commit()
            else:
                lower_ref = _root_commit()

    if lower_ref and upper_ref:
        revision = f'{lower_ref}..{upper_ref}'
    else:
        revision = upper_ref

    commits = _collect_commits(revision)
    if not commits:
        console.print(_('[yellow]No commits found for the selected range.[/yellow]'))
        return

    sections, breakings = _group_commits(commits)
    repo_url = _repo_remote_url() if fmt == 'md' else None

    if fmt == 'text':
        _render_text(sections, breakings)
    else:
        typer.echo(_render_plain(sections, breakings, fmt, repo_url))
