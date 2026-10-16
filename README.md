# hermes-tools

Tools layer for Hermes. The plugin calls any Scalekit connector.

The repository is private until the plugin is ready for the Hermes catalog.
Install asks for three Scalekit values. Copy them from Dashboard, Developers, Settings, API Credentials.

- `SCALEKIT_CLIENT_ID` looks like `skc_1234`.
- `SCALEKIT_CLIENT_SECRET` is the Scalekit account secret. It is not a Gmail or Slack token.
- `SCALEKIT_ENVIRONMENT_URL` looks like `https://your-env.scalekit.dev`.

The plugin creates the identifier, for example `usr_8f3a2c`, and stores it. A missing value stops the plugin and names that value. The plugin does not call Scalekit until all three are set.
