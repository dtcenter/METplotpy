# METplotpy repository conventions

Guidance for AI coding agents working in this repository, and a useful summary
for human contributors.

## Read the Contributor's Guides first

The [METplus Contributor's
Guide](https://metplus.readthedocs.io/en/latest/Contributors_Guide/index.html) covers the process shared by every METplus component.
Its [GitHub Workflow](https://metplus.readthedocs.io/en/latest/Contributors_Guide/github_workflow.html) chapter applies here in full:
how issues, labels, milestones, and project boards are used, how branches are
named, and how pull requests are opened, reviewed, and merged.

The [METplotpy Contributor's
Guide](https://metplus.readthedocs.io/projects/metplotpy/en/latest/Contributors_Guide/index.html),
whose source is `docs/Contributors_Guide/` in this repository, covers adding a
new plot, its tests, and its documentation. METplotpy follows the [METplus
coding standards](https://metplus.readthedocs.io/en/latest/Contributors_Guide/coding_standards.html).

This file is the short form: the steps that are easy to miss. The guides are
authoritative. Where this file and a guide genuinely conflict, say so in the
pull request rather than silently following one.

## Checks that are easy to miss

- A new plot needs pytest tests in a subdirectory of `test/` named for the plot,
  and an entry for those tests in `.github/workflows/unit_tests.yaml`.
- A new plot needs a page in `docs/Users_Guide/`, added to the toctree in
  `docs/Users_Guide/index.rst`.
- A new third-party package goes in `requirements.txt` and in the Python
  Requirements section of `docs/Users_Guide/installation.rst`.

## Pull requests

Fill in `.github/pull_request_template.md`. Change `- [ ]` to `- [x]` on every
item that has been answered or filled in, and leave unanswered items and the
action items under "Pull Request Checklist" unchecked.
