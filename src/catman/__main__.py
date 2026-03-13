from .cli import CatmanShell


def main():
    shell = CatmanShell()
    shell.cmdloop()


if __name__ == "__main__":
    main()
