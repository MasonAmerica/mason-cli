# Mason CLI

The Mason CLI provides command line tools to help you manage your configurations in the Mason
Platform.

The full docs to get started with the Mason Platform are available here:
https://docs.bymason.com/intro/
For docs on using the Mason CLI, see the setup guide here: https://docs.bymason.com/getting-started/

### Using the CLI

Find the [latest release](https://github.com/MasonAmerica/mason-cli/releases/latest) and download
the CLI for your platform under "Assets".

### Developing the CLI

1. Clone this repo: `git clone https://github.com/MasonAmerica/mason-cli.git && cd mason-cli`
1. Build the CLI: `pip3 install mock .`
1. Run the tests: `cd masonlib/test && python3 -m unittest discover .`
