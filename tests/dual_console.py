import subprocess
import sys

p = subprocess.Popen(
    [sys.executable, "-u", "tests/server.py"],
    stdin=subprocess.PIPE,
    text=True,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    bufsize=1
)

assert p.stdin is not None

while True:
    try:
        p.stdin.write(input("Emit event: ") + "\n")
        p.stdin.flush()

    except KeyboardInterrupt:
        break

p.wait()
