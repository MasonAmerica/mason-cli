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

#### Perquisites

1. Install Python 3
1. [Make it the default](https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux#h2-change-python-version-system-wide)
1. Run `pip install virtualenvwrapper`
1. Run `echo "source virtualenvwrapper.sh" > ~/.bashrc`

#### Building the CLI

1. Clone this repo: `git clone https://github.com/MasonAmerica/mason-cli.git && cd mason-cli`
1. Create a virtual environment: `mkvirtualenv mason-cli`
   1. Or use an existing one: `workon mason-cli`
1. Install dependencies: `pip install mock && pip install -e .`

#### Testing the CLI

1. Run `python3 setup.py test`
