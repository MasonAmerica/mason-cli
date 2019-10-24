import os

cli_version = None


def load_version():
    global cli_version

    if not cli_version:
        root = os.path.dirname(os.path.realpath(__file__))
        version_file = os.path.join(root, "VERSION")
        with open(version_file, "r") as f:
            cli_version = f.read().strip()

    return cli_version
