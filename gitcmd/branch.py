import subprocess

def switch(path, tag):
    try:
        result = subprocess.run(
            ["/usr/bin/git", "checkout", "-b", tag],
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        print("RETURN CODE:", e.returncode)
    print("----*******----------" * 5)

    try:
        result = subprocess.run(
            ["/usr/bin/git", "push", "-f", "gitlab", tag],
            cwd=path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )

        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)

    except subprocess.CalledProcessError as e:
        print("❌ Git push failed")
        print("return code:", e.returncode)
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
