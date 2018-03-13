# -*- coding: utf-8 -*-
import logging.handlers
import os
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, BadRequest
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

from Incident import Incident
from Incidents import Incidents
from filters import ScamFilters
from filters import AdminFilters
from config import BOT_TOKEN, admin_channel_id, admins, chats

logdir_path = os.path.dirname(os.path.abspath(__file__))
logfile_path = os.path.join(logdir_path, "logs", "bot.log")

if not os.path.exists(os.path.join(logdir_path, "logs")):
    os.makedirs(os.path.join(logdir_path, "logs"))

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[logfile_handler])
# Add logging.StreamHandler() for stderr debugging purposes

# Check if bot token is valid
if not re.match("[0-9]+:[a-zA-Z0-9\-_]+", BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=BOT_TOKEN)
dp = updater.dispatcher
incidents = Incidents()

for chat_id in chats:
    my_admins = list(admins)
    try:
        for admin in updater.bot.getChatAdministrators(chat_id):
            my_admins.append(admin.user.id)
        admins = set(my_admins)
    except BadRequest:
        text = "Couldn't fetch admins. " \
               "Are you sure the bot is member of chat {}?".format(chat_id)
        logger.error(text)


# Message will be called if spam is detected. The message will be removed
# and the sender will be kicked
def spam_detected(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    logger.info("Detected spam in chat '{}' by user '{}'".format(update.message.chat.title, update.message.from_user.full_name))

    try:
        # ban user from chat
        bot.kickChatMember(chat_id, user_id)
    except TelegramError:
        logger.warning("Not able to kick user {}: {}".format(user_id, update.message))
        # TODO send message to admins so they check it

    try:
        # Delete message
        bot.deleteMessage(chat_id, message_id=update.message.message_id)
    except TelegramError:
        logger.warning("Not able to delete message: {}".format(update.message))
        # TODO send message to admins so they check it


# Method which will be called, when the message could potentially be spam, but
# a human needs to decide
def ask_admins(bot, update):
    # Ask admins if message is spam
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    user_id = update.message.from_user.id

    spam_button = InlineKeyboardButton("Spam", callback_data='{user_id}_{chat_id}_{message_id}_spam'.format(user_id=user_id, chat_id=chat_id, message_id=message_id))
    no_spam_button = InlineKeyboardButton("No Spam", callback_data='{user_id}_{chat_id}_{message_id}_nospam'.format(user_id=user_id, chat_id=chat_id, message_id=message_id))
    reply_markup = InlineKeyboardMarkup([[spam_button, no_spam_button]])

    new_message = bot.forwardMessage(chat_id=admin_channel_id, from_chat_id=chat_id, message_id=message_id)
    admin_message = bot.sendMessage(chat_id=admin_channel_id, text="Is this message spam?", reply_to_message_id=new_message.message_id, reply_markup=reply_markup)

    # Create a new "incident" which will be handled by the admins
    new_incident = Incident(chat_id=chat_id, message_id=message_id, admin_channel_message_id=admin_message.message_id)
    incidents.append(new_incident)


# When a new user joins the group, his name should be checked for frequently
# used scammer names. Often scammers use a pattern like 'Elvira J Joy' or '
# Elly W Wonder', which can easily be detected via RegEx
def check_and_ban_suspicious_users(bot, update):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    for member in update.message.new_chat_members:
        username = member.username if member.username is not None else "no username"

        name = member.full_name
        match = re.search("[A-Za-z]+ ([A-Za-z]{1}) ([A-Za-z]+)", name)

        if match:
            if match.group(1) == match.group(2)[:1]:
                text = "Banned suspected scammer {name} (@{username}) " \
                       "with id {id}".format(name=name,
                                             username=username,
                                             id=member.id)

                try:
                    bot.kickChatMember(chat_id, user_id)
                    logger.info(text)
                except TelegramError as e:
                    logger.error(e)

                    bot.send_message(admin_channel_id, text=text)

    return False


# This function will be called, when someone adds this bot to any group which
# is not mentioned in the AllowedGroups filter
def leave_group(bot, update):
    update.message.reply_text("I am currently only for private use! Goodbye!")
    logger.info("Leaving group '{g_name}' - {g_id}".format(g_name=update.message.chat.title, g_id=update.message.chat.id))
    bot.leaveChat(update.message.chat_id)


def callback_handler(bot, update):
    orig_user_id = update.callback_query.from_user.id
    orig_chat_id = update.callback_query.message.chat.id
    orig_message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id
    data = update.callback_query.data

    # Only admins are allowed to use admin callback functions
    if orig_user_id not in admins:
        logger.error("User {} used admin callback, but not in admin list!".format(orig_user_id))
        return

    # Get the data from the callback_query
    user_id, chat_id, message_id, action = data.split("_")

    # Create a new incident and check if it's still present
    current_incident = Incident(chat_id=chat_id, message_id=message_id)

    if current_incident not in incidents:
        text = "The incident couldn't be found!"
        bot.editMessageText(chat_id=orig_chat_id, message_id=orig_message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
        return

    if action == "spam":
        try:
            # Delete message
            incidents.handle(current_incident)
            text = "Message is spam. I deleted it."
            bot.deleteMessage(chat_id=chat_id, message_id=message_id)
        except TelegramError as e:
            logger.warning("{} - {}".format(chat_id, message_id))
            logger.warning(e)
            text = "Not able to delete message! Maybe already deleted!"
            logger.warning("Not able to delete message: {}. Maybe already deleted or I'm not an admin!".format(message_id))

        text = "Incident handled by {}\n{}".format(update.callback_query.from_user.first_name, text)
        bot.editMessageText(chat_id=orig_chat_id, message_id=orig_message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)

        try:
            bot.kickChatMember(chat_id, user_id)
        except TelegramError:
            text += "\nCouldn't kick user! Maybe he already left!"
            try:
                bot.editMessageText(chat_id=orig_chat_id, message_id=orig_message_id, text=text)
            except:
                pass
            logger.warning("Not able to kick user: {}. Maybe he already left or I'm not an admin!".format(user_id))
    elif action == "nospam":
        incidents.handle(Incident(chat_id=chat_id, message_id=message_id))
        text = "Incident handled by {}\nNo spam. Keeping the message!".format(update.callback_query.from_user.first_name)
        bot.editMessageText(chat_id=orig_chat_id, message_id=orig_message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)


def admin_mention(bot, update):
    if update.message.chat.username is None:
        return

    # for admin in admins:
    bot.sendMessage(admin_channel_id, text="*Someone needs an admin!*\n"
                                           "\n*Chat:* {chat}"
                                           "\n*Name:* {user}"
                                           "\n\n[Direct Link](https://t.me/{g_name}/{m_id})".format(chat=update.message.chat.title,
                                                                                                    user=update.message.from_user.first_name,
                                                                                                    g_name=update.message.chat.username,
                                                                                                    m_id=update.message.message_id),
                    parse_mode="Markdown")


dp.add_handler(MessageHandler(Filters.group & (~ ScamFilters.allowedChatsFilter), leave_group))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.userJoinedFilter, check_and_ban_suspicious_users))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.channelForwardFilter, spam_detected))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.joinChatLinkFilter, spam_detected))
dp.add_handler(MessageHandler(Filters.group & AdminFilters.adminMentionFilter, admin_mention))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.usernameFilter, ask_admins))
dp.add_handler(CallbackQueryHandler(callback_handler))

updater.start_polling()
logger.info("Bot started as  @{}".format(updater.bot.username))
updater.bot.sendMessage(admin_channel_id, text="Bot restarted")
logger.info("Admins are: {}".format(admins))
updater.idle()
