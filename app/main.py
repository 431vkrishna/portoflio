import sys


def main():
    while True:
        sys.stdout.write("$ ")
        command=input()
        if command=="":
            continue
        if command=="exit":
            break
        elif command.startswith("echo "):
            print(command[5:])
        elif command.startswith("type"):
            if command[5:]=="echo" or command[5:]=="type" or command[5:]=="exit":
                print(f"{command[5:]}: is a shell builtin")
            else :
                print(f"{command[5:]}: not found")

        else :
            print(f"{command}: command not found")




if __name__ == "__main__":
    main()
