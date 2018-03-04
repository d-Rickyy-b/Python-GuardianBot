# Python-GuardianBot
This bot was designed for keeping spam and ads out of your public Telegram groups. It helps you by searching through all of the specified groups' messages. Keep in mind that the bot needs to have "privacy mode" switched off via [@BotFather](https://t.me/BotFather), to check all the messages.

As currently configured, it automatically removes all the "joinchat" links and all not-whitelisted forwards to your group chats by default. You can host your own instance of this bot e.g. on your own VPS.

### Using it for your own group
If you want to use this bot for your own groups, you need to host it yourself. There is no publically available **hosted** version of this bot.

First you need to configure the bot accordingly (see [Configuration](#configuration)). After that you need to add it to your group. If you want to change the way the bot works, just add another Filter to the `MessageFilters` directory. Since this bot uses the [python-telegram-bot Framework](https://github.com/python-telegram-bot/python-telegram-bot), you can use [their instructions](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Advanced-Filters) on how to create filters.

It requires some programming skills, but you should be able to do that even if you have never done much programming yourself.

### Configuration
The bot needs a little configuration file called config.py. It contains basic configuration such as the bot token, the admin channel, allowed groups, and much more.

You can find a sample configuration file [here](https://gist.github.com/d-Rickyy-b/65fde2038928b8b43e4bd6307334eb92). Below is a short explanation of the configuration variables.

| Variable name | Type | Description |
| ------------- | ---- | ----------- |
| `BOT_TOKEN`   | str  | The bot token you receive from BotFather. |
| `admin_channel_id` | int | The id of the admin channel, into which the bot posts suspicious messages. |
| `admins` | list(int) | List of ids of users which are considered "admin" of the bot. Admins can delete suspicious messages, reported to the admin channel. |
| `chats` | list(int) | List of chat ids, in which the bot should look for bot admins. Each group admin is considered bot admin. |
| `whitelisted_chats` | list(int) | A list of chat ids, into which the bot can be added. The bot will leave all other chats. |
| `whitelisted_groups` | list(int) | A list of group ids, from which forwarded messages are allowed. Messages forwarded from other groups are considered spam. |
| `whitelisted_channels` | list(int) | A list of channel ids, from which forwarded messages are allowed. Messages forwarded from other channels are considered spam. |
