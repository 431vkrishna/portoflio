import subprocess
import sys
import os
import shlex
import readline

BUILTINS = {"exit", "echo", "type", "pwd", "cd"}


def display_matches_hook(substitution, matches, longest_match_length):
    print()
    print("  ".join(matches))
    sys.stdout.write("$ " + readline.get_line_buffer())
    sys.stdout.flush()


def completer(text, state):
    builtin_matches = [cmd for cmd in BUILTINS if cmd.startswith(text)]
    exe_matches = find_executable(text, autocomplete=True)
    matches = sorted(set(builtin_matches + exe_matches))
    if state < len(matches):
        return matches[state] + " "
    return None


readline.set_completer(completer)
readline.parse_and_bind("tab: complete")
readline.set_completion_display_matches_hook(display_matches_hook)


def find_executable(cmd, autocomplete=False):
    path_dirs = os.environ.get("PATH", "").split(":")
    matches = []
    for directory in path_dirs:
        if not os.path.isdir(directory):
            continue
        if autocomplete:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if (file.startswith(cmd)):
                    matches.append(file)
        else:
            full_path = os.path.join(directory, cmd)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path

    return matches if autocomplete else None


def run_builtin(parts, input_data=None):
    cmd = parts[0]
    if cmd == "echo":
        return " ".join(parts[1:]) + "\n"
    elif cmd == "type":
        target = parts[1]

        if target in BUILTINS:
            return f"{target} is a shell builtin\n"

        else:
            path = find_executable(target)

            if path:
                return f"{target} is {path}\n"
            else:
                return f"{target}: not found\n"


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()

        if not command:
            continue

        parts = shlex.split(command)
        cmd = parts[0]

        if cmd == "exit":
            break

        elif "|" in command:
            cmds = [shlex.split(part.strip()) for part in command.split("|")]
            processes = []
            prev_stdout = None

            for i, cmd in enumerate(cmds):
                if cmd[0] in BUILTINS:
                    input_data = None
                    if prev_stdout is not None:
                        input_data = prev_stdout.read()
                        prev_stdout.close()
                        prev_stdout = None

                    output = run_builtin(cmd, input_data)

                    if i == len(cmds) - 1:
                        sys.stdout.write(output)
                        sys.stdout.flush()
                    else:
                        p = subprocess.Popen(
                            ["cat"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            text=True,
                        )
                        assert p.stdin is not None
                        assert p.stdout is not None
                        p.stdin.write(output)
                        p.stdin.close()
                        prev_stdout = p.stdout
                        processes.append(p)
                else:
                    p = subprocess.Popen(
                        cmd,
                        stdin=prev_stdout,
                        stdout=subprocess.PIPE if i < len(cmds) - 1 else None,
                        text=True,
                    )
                    if prev_stdout is not None:
                        prev_stdout.close()
                    prev_stdout = p.stdout
                    processes.append(p)

            if processes and processes[-1].stdout is not None:
                for line in processes[-1].stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()

            for p in processes:
                p.wait()

        elif cmd == "echo":

            stdout_redirect = None
            stderr_redirect = None
            append_mode = False

            if ">" in parts:
                idx = parts.index(">")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if ">>" in parts:
                idx = parts.index(">>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            if "1>" in parts:
                idx = parts.index("1>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if "1>>" in parts:
                idx = parts.index("1>>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            if "2>" in parts:
                idx = parts.index("2>")
                stderr_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if "2>>" in parts:
                idx = parts.index("2>>")
                stderr_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            output = " ".join(parts[1:])

            mode = "a" if append_mode else "w"

            if stderr_redirect:
                open(stderr_redirect, mode).close()
            if stdout_redirect:
                with open(stdout_redirect, mode) as f:
                    f.write(output + "\n")
            else:
                print(output)

        elif cmd == "pwd":
            print(os.getcwd())

        elif cmd == "cd":
            if len(parts) == 1:
                home = os.environ.get("HOME")
                if home:
                    os.chdir(home)
            else:
                path = parts[1]
                if path == '~':
                    path = os.environ.get("HOME")
                try:
                    os.chdir(path)
                except FileNotFoundError:
                    print(f"cd: {path}: No such file or directory")



        elif cmd == "type":

            if len(parts) < 2:
                continue

            target = parts[1]

            if target in BUILTINS:
                print(f"{target} is a shell builtin")

            else:
                path = find_executable(target)

                if path:
                    print(f"{target} is {path}")
                else:
                    print(f"{target}: not found")

        else:
            append_mode = False
            stderr_redirect = None
            stdout_redirect = None

            if ">" in parts:
                idx = parts.index(">")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if ">>" in parts:
                idx = parts.index(">>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            if "1>" in parts:
                idx = parts.index("1>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if "1>>" in parts:
                idx = parts.index("1>>")
                stdout_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            if "2>" in parts:
                idx = parts.index("2>")
                stderr_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = False

            if "2>>" in parts:
                idx = parts.index("2>>")
                stderr_redirect = parts[idx + 1]
                parts = parts[:idx]
                append_mode = True

            path = find_executable(cmd)
            mode = "a" if append_mode else "w"

            if path:
                stdout_file = open(stdout_redirect, mode) if stdout_redirect else None
                stderr_file = open(stderr_redirect, mode) if stderr_redirect else None

                subprocess.run([cmd] + parts[1:], stdout=stdout_file, stderr=stderr_file)
                if stdout_file:
                    stdout_file.close()
                if stderr_file:
                    stderr_file.close()
            else:
                print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()