import subprocess

result = subprocess.run(
    ["git", "push", "gitlab", "hexinos16.0.1", ],
    cwd="/home/hl/aosp/lineageos23/external/android_onboarding",
    capture_output=True,
    text=True,
    check=True
)

print(result.stdout)
