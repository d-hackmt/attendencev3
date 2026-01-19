# Attendence/services/github_service.py
from github import GithubException
from Attendence.core.clients import create_github_repo
from Attendence.core.logger import get_logger
from Attendence.core.utils import current_ist_date

logger = get_logger(__name__)

def push_attendance_matrix(class_name, csv_content):
    """
    Pushes the attendance matrix CSV to the configured GitHub repo.
    Returns: (success: bool, message: str)
    """
    try:
        gh, repo = create_github_repo()
        if not repo:
            return False, "GitHub not configured."

        filename = f"records/attendance_matrix_{class_name}_{current_ist_date().replace('-', '')}.csv"
        commit_message = f"Push matrix for {class_name}"
        branch = "main"

        try:
            existing_file = repo.get_contents(filename, ref=branch)
            repo.update_file(
                path=filename,
                message=commit_message,
                content=csv_content,
                sha=existing_file.sha,
                branch=branch
            )
            return True, f"Updated existing file: {filename}"
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=filename,
                    message=commit_message,
                    content=csv_content,
                    branch=branch
                )
                return True, f"Created new file: {filename}"
            else:
                logger.exception("GitHub exception")
                return False, f"GitHub Error: {getattr(e, 'data', str(e))}"

    except Exception as e:
        logger.exception("Failed to push to GitHub")
        return False, f"Failed to push: {str(e)}"
