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
1. Run `echo "source virtualenvwrapper.sh" >> ~/.bashrc`

#### Building the CLI

1. Clone this repo: `git clone https://github.com/MasonAmerica/mason-cli.git && cd mason-cli`
1. Create a virtual environment: `mkvirtualenv mason-cli`
   1. Or use an existing one: `workon mason-cli`
1. Install dependencies: `pip install mock && pip install -e .`

#### Testing the CLI

All behavior changes and bug fixes should come with associated test changes. While you can manually
run tests with `python3 setup.py test`, the best way to do so is with IntelliJ's
[Auto Test](https://www.jetbrains.com/help/idea/monitoring-and-managing-tests.html) feature which
continuously tests your code as you write it. Just run all tests in the `tests` folder.

#### Cutting a release

The release process is automated using tag pushes.

1. Create a commit called `v$VERSION` which sets the CLI version inside the `VERSION` file at the
   root of this repository.
   - The commit message will be used as release notes for this CLI release.
1. Create a tag for that commit and call it `$VERSION`.
1. Push both the commit and tag to master.

For an example, see e50d6981a77e5d1a363cb5a8c97a644a07aaabfb.
