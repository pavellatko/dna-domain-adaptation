from operator import xor
import subprocess


def cmdrun(
    cmd: str,
    input: bytes = None,
    stdout=None,
    shell: bool = False,
    capture_output: bool = True,
):
    return subprocess.run(
        cmd if shell else cmd.split(),
        input=input,
        stdout=stdout,
        check=True,
        shell=shell,
        capture_output=capture_output and (stdout is None),
    )
