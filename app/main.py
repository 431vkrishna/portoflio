import sys


def main():
    sys.stdout.write("$ ")
    pass

    command=input()
    print(f"{command}: command not found")

    while True:
        command = input()
        print(f"{command}: command not found")
        print("$ ",end="")

if __name__ == "__main__":
    main()
