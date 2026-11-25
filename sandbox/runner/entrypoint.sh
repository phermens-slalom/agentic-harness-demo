#!/bin/sh
# Inputs (env): REPO, BRANCH, ISSUE_JSON, PLAN_JSON, FEEDBACK, GITHUB_TOKEN (short-lived, from Secret Manager)
set -eu
git clone --depth 50 "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git" repo
cd repo
git checkout -B "$BRANCH"
# TODO: invoke the coding agent headless with AGENTS.md + plan + feedback as the prompt,
#       run the repo's test command from AGENTS.md, commit, push, open/update PR via API.
echo "sandbox runner stub: implement in week 2"
