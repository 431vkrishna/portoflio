import os
import sys
import shlex
import shutil
import subprocess
import time

try:
    import readline

    HAS_READLINE = True
except ImportError:
    try:
        import pyreadline3 as readline

        HAS_READLINE = True
    except ImportError:
        HAS_READLINE = False


def main():
    builtins = ["echo", "exit", "type", "pwd", "cd", "jobs"]

    jobs = {}

    def completer(text, state):
        candidates = []
        for b in builtins:
            if b.startswith(text):
                candidates.append(b + " ")
        if not candidates:
            for directory in os.environ.get("PATH", "").split(os.pathsep):
                try:
                    for name in os.listdir(directory):
                        if name.startswith(text):
                            full = os.path.join(directory, name)
                            if os.access(full, os.X_OK):
                                candidates.append(name + " ")
                except FileNotFoundError:
                    continue
        candidates = sorted(set(candidates))
        if state < len(candidates):
            return candidates[state]
        return None

    if HAS_READLINE:
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

    def get_marker(jnum, all_nums):
        if jnum == all_nums[-1]:
            return "+"
        elif len(all_nums) >= 2 and jnum == all_nums[-2]:
            return "-"
        return " "

    def reap_jobs():
        """Check all jobs, print Done for completed ones, remove them."""
        sorted_nums = sorted(jobs.keys())
        done_nums = [n for n in sorted_nums if jobs[n][0].poll() is not None]
        if not done_nums:
            return
        for jnum in sorted_nums:
            proc, jcmd = jobs[jnum]
            if proc.poll() is None:
                continue
            marker = get_marker(jnum, sorted_nums)
            status_field = f"{'Done':<24}"
            print(f"[{jnum}]{marker}  {status_field}{jcmd}")
        for jnum in done_nums:
            del jobs[jnum]

    def wait_for_reap(timeout=0.5, interval=0.05):
        """Briefly poll for newly completed jobs before showing the prompt."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            any_done = any(proc.poll() is not None for proc, _ in jobs.values())
            if any_done:
                break
            time.sleep(interval)
        reap_jobs()

    while True:
        # Reap completed jobs before showing each prompt
        # Use wait_for_reap so recently-finished processes are caught
        wait_for_reap()

        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            command = input()
        except EOFError:
            break

        if not command.strip():
            continue

        parts = shlex.split(command)

        background = False
        if parts and parts[-1] == "&":
            background = True
            parts = parts[:-1]

        stdout_file = None
        stderr_file = None
        append_stdout = False
        append_stderr = False

        if ">>" in parts:
            idx = parts.index(">>")
            stdout_file = parts[idx + 1]
            append_stdout = True
            parts = parts[:idx]
        elif "1>>" in parts:
            idx = parts.index("1>>")
            stdout_file = parts[idx + 1]
            append_stdout = True
            parts = parts[:idx]
        elif ">" in parts:
            idx = parts.index(">")
            stdout_file = parts[idx + 1]
            parts = parts[:idx]
        elif "1>" in parts:
            idx = parts.index("1>")
            stdout_file = parts[idx + 1]
            parts = parts[:idx]
        elif "2>>" in parts:
            idx = parts.index("2>>")
            stderr_file = parts[idx + 1]
            append_stderr = True
            parts = parts[:idx]
        elif "2>" in parts:
            idx = parts.index("2>")
            stderr_file = parts[idx + 1]
            parts = parts[:idx]

        if not parts:
            continue

        cmd = parts[0]

        stdout_mode = "a" if append_stdout else "w"
        stderr_mode = "a" if append_stderr else "w"

        if cmd == "exit":
            break

        elif cmd == "echo":
            output = " ".join(parts[1:])
            if stderr_file:
                open(stderr_file, stderr_mode).close()
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + "\n")
            else:
                print(output)

        elif cmd == "pwd":
            output = os.getcwd()
            if stderr_file:
                open(stderr_file, stderr_mode).close()
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + "\n")
            else:
                print(output)

        elif cmd == "cd":
            if len(parts) < 2:
                continue
            directory = parts[1]
            if directory == "~":
                directory = os.path.expanduser("~")
            try:
                os.chdir(directory)
            except FileNotFoundError:
                error = f"cd: {directory}: No such file or directory"
                if stderr_file:
                    with open(stderr_file, stderr_mode) as f:
                        f.write(error + "\n")
                else:
                    print(error)

        elif cmd == "jobs":
            sorted_nums = sorted(jobs.keys())
            done_nums = [n for n in sorted_nums if jobs[n][0].poll() is not None]
            all_displayed = sorted_nums
            for jnum in all_displayed:
                proc, jcmd = jobs[jnum]
                is_done = proc.poll() is not None
                marker = get_marker(jnum, all_displayed)
                if is_done:
                    status_field = f"{'Done':<24}"
                    print(f"[{jnum}]{marker}  {status_field}{jcmd}")
                else:
                    status_field = f"{'Running':<24}"
                    print(f"[{jnum}]{marker}  {status_field}{jcmd} &")
            for jnum in done_nums:
                del jobs[jnum]

        elif cmd == "type":
            if len(parts) < 2:
                continue
            target = parts[1]
            if target in builtins:
                output = f"{target} is a shell builtin"
            else:
                path = shutil.which(target)
                if path:
                    output = f"{target} is {path}"
                else:
                    output = f"{target}: not found"
            if stderr_file:
                open(stderr_file, stderr_mode).close()
            if stdout_file:
                with open(stdout_file, stdout_mode) as f:
                    f.write(output + "\n")
            else:
                print(output)

        else:
            if shutil.which(cmd):
                if background:
                    out_handle = None
                    err_handle = None
                    try:
                        if stdout_file:
                            out_handle = open(stdout_file, stdout_mode)
                        if stderr_file:
                            err_handle = open(stderr_file, stderr_mode)
                        proc = subprocess.Popen(
                            parts,
                            stdout=out_handle,
                            stderr=err_handle,
                        )
                        job_number = (max(jobs.keys()) + 1) if jobs else 1
                        jobs[job_number] = (proc, " ".join(parts))
                        print(f"[{job_number}] {proc.pid}")
                    finally:
                        if out_handle:
                            out_handle.close()
                        if err_handle:
                            err_handle.close()
                else:
                    out_handle = None
                    err_handle = None
                    try:
                        if stdout_file:
                            out_handle = open(stdout_file, stdout_mode)
                        if stderr_file:
                            err_handle = open(stderr_file, stderr_mode)
                        subprocess.run(
                            parts,
                            stdout=out_handle,
                            stderr=err_handle,
                        )
                    finally:
                        if out_handle:
                            out_handle.close()
                        if err_handle:
                            err_handle.close()
            else:
                error = f"{cmd}: command not found"
                if stderr_file:
                    with open(stderr_file, stderr_mode) as f:
                        f.write(error + "\n")
                else:
                    print(error)


if __name__ == "__main__":
    main()
