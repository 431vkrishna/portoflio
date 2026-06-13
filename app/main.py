import sys
import shutil
import os


def main():
    while True:
        sys.stdout.write("$ ")
        command=input()
        if command=="":
            continue
        if command=="exit":
            break
        elif command=="pwd":
            print(os.getcwd())
        elif command.startswith("echo "):
            print(command[5:])
        elif command.startswith("type"):
            cmd,arg_0,*args=command.strip().split()
            if command.endswith("echo") or command.endswith("type") or command.endswith("exit"):
                print(f"{command[5:]} is a shell builtin")
            elif shutil.which(arg_0):
                print(f"{arg_0} is {shutil.which(arg_0)}")
            else:
                print(f"{command[5:]}: not found")


        else :
            print(f"{command}: command not found")




if __name__ == "__main__":
    main()
