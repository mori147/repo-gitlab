import subprocess

from config import s20


def status(path):
    result = subprocess.run(
        ["/usr/bin/git", "status"],
        cwd=path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    return "nothing to commit" in result.stdout
