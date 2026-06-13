import os
import sys
import subprocess

builtins = ["echo", "exit", "type", "pwd"]


def find_executable(cmd):
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        path = os.path.join(directory, cmd)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def main():
    while True:
        command = input("$ ")
        parts = command.split()
        cmd, args = parts[0], parts[1:]
        match cmd:
            case "exit":
                break
            case "echo":
                print(" ".join(args))
            case "pwd":
                print(os.getcwd())
            case "type":
                target = args[0]
                if target in builtins:
                    print(f"{target} is a shell builtin")
                elif path := find_executable(target):
                    print(f"{target} is {path}")
                else:
                    print(f"{target}: not found")
            case _:
                if path := find_executable(cmd):
                    subprocess.run([cmd] + args, executable=path)
                else:
                    print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()