"""A module for measuring the time it takes to merge a GitHub pull request.

This module provides functions for measuring the time it takes to merge a GitHub pull
request, as well as calculating the average time to merge for a list of pull requests.

Functions:
    measure_time_to_merge(
        pull_request: github3.pulls.PullRequest,
        ready_for_review_at: Union[datetime, None]
    ) -> Union[timedelta, None]:
        Measure the time it takes to merge a pull request.

"""

from datetime import datetime, timedelta
import os
from typing import Union

import github3


def measure_time_to_merge(
    pull_request: github3.pulls.PullRequest, ready_for_review_at: Union[datetime, None]
) -> Union[timedelta, None]:
    """Measure the time it takes to merge a pull request.

    Args:
        pull_request (github3.pulls.PullRequest): A GitHub pull request.
        ready_for_review_at (Union[timedelta, None]): When the PR was marked as ready for review

    Returns:
        Union[datetime.timedelta, None]: The time it takes to close the issue.

    """
    merged_at = None
    if pull_request.merged_at is None:
        return None

    merged_at = pull_request.merged_at

    if ready_for_review_at:
        return merged_at - ready_for_review_at

    created_at = pull_request.created_at
    return merged_at - created_at



def fetch_pull_requests(repo):
    return repo.pull_requests(state='closed', number=-1)


def generate_report(prs_with_metrics, average_time_to_merge, total_open_prs, count):
    with open("pr_metrics.md", "w", encoding="utf-8") as file:
        file.write("# PR Metrics\n\n")
        file.write("| PR | Ready for Review | Merged At | Total Time Taken |\n")
        file.write("| --- | --- | --- | --- |\n")
        for pr_metric in prs_with_metrics:
            file.write(f"| {pr_metric['pr']} | {pr_metric['ready_for_review_at']} | {pr_metric['merged_at']} | {pr_metric['time_to_merge']} |\n")
        file.write(f"\n**Average Time to Merge:** {average_time_to_merge}\n")
        file.write(f"\n**Total Open PRs:** {total_open_prs}\n")
        file.write(f"\n**Total Closed PRs:** {count}\n")
    print("Wrote PR metrics to pr_metrics.md")


def main():
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REPO_NAME = "zerodha/zerodhatech.github.io"

    gh = github3.login(token=GITHUB_TOKEN)
    repo = gh.repository(*REPO_NAME.split('/'))
    pull_requests = fetch_pull_requests(repo)

    prs_with_metrics = []
    total_time_to_merge = timedelta(0)
    count = 0

    for pr in pull_requests:
        ready_for_review_at = pr.created_at if not pr.draft else pr.updated_at
        time_to_merge = measure_time_to_merge(pr, ready_for_review_at)
        if time_to_merge:
            prs_with_metrics.append({
                'pr': pr.number,
                'ready_for_review_at': ready_for_review_at,
                'merged_at': pr.merged_at,
                'time_to_merge': time_to_merge
            })
            total_time_to_merge += time_to_merge
            count += 1

    average_time_to_merge = total_time_to_merge / count if count > 0 else timedelta(0)
    total_open_prs = repo.pull_requests(state='open', number=-1).count
    generate_report(prs_with_metrics, average_time_to_merge, total_open_prs, count)

if __name__ == "__main__":
    main()