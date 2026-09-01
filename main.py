from pathlib import Path
import subprocess
import time
import random

DATA_FILE = Path("data.txt")
PUSH_RETRY_DELAY = 5


def run_git(*args: str) -> None:
    """Run a Git command and raise an error if it fails."""
    subprocess.run(["git", *args], check=True)


def increment_value() -> None:
    """Read the integer in data.txt, increment it, and save it."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} does not exist.")

    content = DATA_FILE.read_text(encoding="utf-8").strip()

    try:
        value = int(content)
    except ValueError as exc:
        raise ValueError(
            f"{DATA_FILE} must contain a single integer."
        ) from exc

    DATA_FILE.write_text(f"{value + 1}\n", encoding="utf-8")


def has_uncommitted_changes() -> bool:
    """Return True if there are uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(result.stdout.strip())


def push_until_success() -> None:
    """Keep trying to push until it succeeds."""
    while True:
        try:
            run_git("push", "origin", "master")
            print("Push successful.")
            return
        except subprocess.CalledProcessError:
            print(
                f"Push failed. Retrying in {PUSH_RETRY_DELAY} seconds..."
            )
            time.sleep(PUSH_RETRY_DELAY)


def main() -> None:
    # Only make a new increment/commit if there are no
    # uncommitted changes waiting to be pushed.
    for i in range (random.randint(1,10)+1):

            
        increment_value()

        run_git("add", str(DATA_FILE))
        run_git("commit", "-m", "Increment data value")

        # If the internet is unavailable, this keeps retrying
        # the SAME commit instead of creating new commits.
    if has_uncommitted_changes():
       push_until_success()


if __name__ == "__main__":
    main()
