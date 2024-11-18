# slack-telescope

Installation instructions:
1. Clone this repository and create a ".env" file in the root directory
2. Create a new Slack app [here](https://api.slack.com/apps) by clicking on "Create New App"
3. Choose "From a manifest" and paste in the included app_manifest.json
4. Copy the Signing Secret into ".env" prefixed by "SIGNING_SECRET="
5. Under App-Level Tokens select "Generate Token and Scopes", name it "telescope-socket" and add the "connections:write" scope
6. Copy the new token into ".env" prefixed by "SLACK_APP_TOKEN="
7. Navigate to Install App on the side bar, and install the app into your Slack Workspace
8. Copy the Bot User OAuth Token into ".env" prefixed by "SLACK_BOT_TOKEN="
9. Create a private #observatory channel and public #telescopes channel
10. Set the OBSERVATORY_CHANNEL_ID and BROADCAST_CHANNEL_ID in app/config.py with the ids of the channels you just created
11. Start the Telescope bot by running `python -m app` from the root project directory
12. (Optional) Automate the bot using the provided slack-telescope.service file