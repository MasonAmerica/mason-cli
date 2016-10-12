# mason-cli

  mason-cli provides command line interfaces that allow you to publish,
  query, and deploy your configurations and packages to your devices in the
  field.

  Type `mason --help` for more details

## mason auth

`mason auth` provides a means to authenticate against mason services via username and password.

```sh
mason auth [OPTIONS]
```

## mason publish

`mason-cli publish` provides a means to publish artifacts to mason's registry service, so that they can be
deployed to your devices in the field.

```sh
mason publish [OPTIONS] ARTIFACT
```
