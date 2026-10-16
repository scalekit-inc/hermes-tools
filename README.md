# hermes-tools

Tools layer for Hermes. The plugin calls any Scalekit connector.

The repository is private until the plugin is ready for the Hermes catalog.
Install asks for four Scalekit values:

- `SCALEKIT_CLIENT_ID`
- `SCALEKIT_CLIENT_SECRET`
- `SCALEKIT_ENVIRONMENT_URL`
- `SCALEKIT_IDENTIFIER`

A missing value stops the plugin and names that value. The plugin does not call Scalekit until all four are set.
