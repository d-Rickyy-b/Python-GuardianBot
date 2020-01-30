BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
USE_WEBHOOK = False
WEBHOOK_PORT = 9001
WEBHOOK_URL = "https://domain.example.com/" + BOT_TOKEN
CERTPATH = "/etc/certs/example.com/fullchain.cer"

admin_channel_id = 123456789
admins = [1122334455, 11224455]
chats = [-123456789123456]

# Bans a user if there are 5 messages in 10 seconds
flood_nr_of_msgs = 5
flood_time_in_secs = 10

allowed_usernames = ["@publictestgroup", "@snowballfight"]

# Allowed chats for AllowedChatsFilter
whitelisted_chats = [-1001234567891, -1001235557890, -1001234447899]

# Allowed channels for ChannelForwardFilter
whitelisted_channels = [-1001234567900, -1001234567901, -1001234567902]

# Allowed chats for GroupForwardFilter
whitelisted_groups = [-1001234568765]
