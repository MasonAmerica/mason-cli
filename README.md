# The Mason Command Line tools (mason-cli)

The Mason Command Line tools (or `mason-cli`) provides command line interfaces that allow you to publish, query, and deploy your configurations and packages to your devices in the field.

## Requirements

In order to use Mason CLI, you will need Python to be setup correctly on your system. Mason CLI has been currently tested on Python 2.7.x.

> NOTE: On OSX we recommend installing Python via the `brew` package manager to avoid the need for `sudo`.

Once Python is setup, you will need to ensure `pip` is available. You can install `pip` by following the instructions [here](https://pip.pypa.io/en/stable/installing/). Once `pip` is available, install Mason CLI as follows:

```bash
pip install git+ssh://git@github.com/MasonAmerica/mason-cli.git
```

> NOTE: On Linux, you may need to run the above command as the root user by prefixing with `sudo`.

To verify installation, you can type `mason` to see the following output:

```
Usage: mason [OPTIONS] COMMAND [ARGS]...

  mason-cli provides command line interfaces that allow you to publish,
  query, and deploy your configurations and packages to your devices in the
  field.

Options:
  --verbose
  --access_token TEXT  optional access token if already available
  --id_token TEXT      optional id token if already available
  --help               Show this message and exit.

Commands:
  login      Authenticate via user/password
  logout    Log out of current session
  register  Register artifacts to the mason platform
  version   Display mason-cli version
```

## Usage

In order to use Mason CLI, you will need credentials to authenticate against the Mason Services. Please contact Mason Support to ensure that you have a Mason account configured already. You will need a username and a password to proceed.

Type `mason --help` for details on available commands. The various individual commands are described below.

### mason login

`mason login` provides a means to authenticate against Mason Services via username and password. This only needs to be run once; the tool will securely cache the credentials locally to ensure you can re-run the tool without having to reauthenticate each time.

```sh
mason login [OPTIONS]
```

Enter your username and password to ensure your credentials are saved for future runs:
```
$ mason login
User: user@example.tld
Password: *********
User authenticated.
```

### mason register

`mason register` provides a means to register artifacts to mason's Registry Service, so that they can be deployed to your devices in the field. Currently the tool supports publishing Android packages (APKs) and bootanimations that have already been configured during the pilot/development phase. The purpose of this command is to publish a newer version of an artifact to replace an existing one of an older version.

```
mason register --help

Usage: mason register [OPTIONS] COMMAND [ARGS]...

  Register artifacts to the mason platform

Options:
  -s, --skip-verify  skip verification of artifact details
  --help             Show this message and exit.

Commands:
  apk     Register apk artifacts
  config  Register config artifacts
  media   Register media artifacts
```

`mason register apk` for apk publishes

```
mason register apk --help

Usage: mason register apk [OPTIONS] APK

  Register apk artifacts

Options:
  --help  Show this message and exit.
```

`mason register media` for media publishes

```
Usage: mason register media [OPTIONS] BINARY

  Register media artifacts

Options:
  -n, --name TEXT
  -t, --type TEXT
  -v, --version TEXT
  --help Show this message and exit.
```

`mason register config` for config publishes

```
Usage: mason register config [OPTIONS] YAML

  Register config artifacts

Options:
  --help  Show this message and exit.
```

### Notes

A register operation will cause the artifact to immediately go live -- the next successful check-in from a device against the Mason Services will result in the artifact being retrieved and installed.

When you register an apk artifact, you must ensure that:

* it is signed with the same signing certificate as the original application that was preinstalled on all devices

* the `versionCode` is larger than the previous value. It is recommended that you also change the `versionName` for debugging purposes

The following is an example of publishing a newer version of an existing APK, to be pushed to all devices associated with your Mason account:
```
$ mason publish android-4.8.201.apk
------------ APK ------------
File Name: android-4.8.201.apk
File size:  760679
Package: com.google.zxing.client.android
Version Name: 4.8.201 (beta)
Version Code: 201
-----------------------------
Continue publish? (y)
Requesting user info...
Connecting to server...
Uploading artifact...
100% |#########################################################################|
File upload complete.
Registering to mason services...
Artifact registered.
```
