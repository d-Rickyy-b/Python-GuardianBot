# -*- coding: utf-8 -*-
import logging.handlers
import os
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, BadRequest
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

import config
from FloodBuffer import FloodBuffer
from Incident import Incident
from Incidents import Incidents
from filters import AdminFilters
from filters import ScamFilters

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
if not re.match(r"[0-9]+:[a-zA-Z0-9\-_]+", config.BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=config.BOT_TOKEN, use_context=True)
dp = updater.dispatcher
incidents = Incidents()
floodBuffer = FloodBuffer()
channel_admins = []


# Has no real use for now. Can be used to contact admins in private
def reload_admins():
    global channel_admins
    for chat_id in config.chats:
        my_admins = list(config.admins)
        try:
            for admin in updater.bot.getChatAdministrators(chat_id):
                my_admins.append(admin.user.id)
            channel_admins = set(my_admins)
        except BadRequest:
            text = "Couldn't fetch admins. " \
                   "Are you sure the bot is member of chat {}?".format(chat_id)
            logger.error(text)


# Message will be called if spam is detected. The message will be removed
# and the sender will be kicked
def scam_detected(update, context):
    chat_id = update.effective_message.chat_id
    user = update.effective_message.from_user
    bot = context.bot

    scam_found = "Detected scam in chat @{} by user '{}' - @{}. Kicking user for scam.".format(update.message.chat.username, user.full_name, user.username)
    logger.info(scam_found)
    bot.send_message(config.admin_channel_id, scam_found)

    try:
        # ban user from chat
        bot.kickChatMember(chat_id, user.id)
    except TelegramError:
        error_msg = "Not able to kick user {}: {}".format(user.id, update.message)
        logger.warning(error_msg)
        bot.send_message(config.admin_channel_id, error_msg)

    try:
        # Delete message
        bot.deleteMessage(chat_id, message_id=update.message.message_id)
    except TelegramError:
        logger.warning("Not able to delete message: {}".format(update.message))
        warn_msg = "Warning - message could not be deleted. " \
                   "[Please Check!](https://t.me/{g_name}/{m_id})".format(chat=update.message.chat.title,
                                                                          user=update.message.from_user.first_name,
                                                                          g_name=update.message.chat.username,
                                                                          m_id=update.message.message_id)
        bot.send_message(config.admin_channel_id, warn_msg)


# Method which will be called, when the message could potentially be spam, but
# a human needs to decide
def ask_admins(update, context):
    # Ask admins if message is spam
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    user_id = update.message.from_user.id
    bot = context.bot

    spam_button = InlineKeyboardButton("Spam", callback_data='{user_id}_{chat_id}_{message_id}_spam'.format(user_id=user_id, chat_id=chat_id, message_id=message_id))
    no_spam_button = InlineKeyboardButton("No Spam", callback_data='{user_id}_{chat_id}_{message_id}_nospam'.format(user_id=user_id, chat_id=chat_id, message_id=message_id))
    reply_markup = InlineKeyboardMarkup([[spam_button, no_spam_button]])

    direct_link = "\n\n[Direct Link](https://t.me/{g_name}/{m_id})".format(
        g_name=update.message.chat.username,
        m_id=update.message.message_id)

    new_message = bot.forwardMessage(chat_id=config.admin_channel_id,
                                     from_chat_id=chat_id,
                                     message_id=message_id)

    admin_message = bot.sendMessage(chat_id=config.admin_channel_id, text="Is this message spam?" + direct_link,
                                    reply_to_message_id=new_message.message_id,
                                    reply_markup=reply_markup,
                                    disable_web_page_preview=True,
                                    parse_mode="Markdown")

    # Create a new "incident" which will be handled by the admins
    new_incident = Incident(chat_id=chat_id, message_id=message_id, admin_channel_message_id=admin_message.message_id)
    incidents.append(new_incident)


# Method to notify admins about stuff
def notify_admins(text):
    updater.bot.send_message(config.admin_channel_id, text=text)


# When a new user joins the group, his name should be checked for frequently
# used scammer names. Often scammers use a pattern like 'Elvira J Joy' or '
# Elly W Wonder', which can easily be detected via RegEx
def check_and_ban_suspicious_users(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    bot = context.bot

    for member in update.message.new_chat_members:
        username = member.username if member.username is not None else "no username"

        name = member.full_name
        match = re.search("[A-Za-z]+ ([A-Za-z]) ([A-Za-z]+)", name)

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

                    bot.send_message(config.admin_channel_id, text=text)

    return False


# This function will be called, when someone adds this bot to any group which
# is not mentioned in the AllowedGroups filter
def leave_group(update, context):
    update.message.reply_text("I am currently only for private use! Goodbye!")
    logger.info("Leaving group '{g_name}' - {g_id}".format(g_name=update.message.chat.title, g_id=update.message.chat.id))
    context.bot.leaveChat(update.message.chat_id)


def callback_handler(update, context):
    orig_user_id = update.callback_query.from_user.id
    orig_chat_id = update.callback_query.message.chat.id
    orig_message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id
    data = update.callback_query.data
    bot = context.bot

    # Only admins are allowed to use admin callback functions
    if orig_user_id not in config.admins:
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
            except Exception as e:
                logger.error(e)
            logger.warning("Not able to kick user: {}. Maybe he already left or I'm not an admin!".format(user_id))
    elif action == "nospam":
        incidents.handle(Incident(chat_id=chat_id, message_id=message_id))
        text = "Incident handled by {}\nNo spam. Keeping the message!".format(update.callback_query.from_user.first_name)
        bot.editMessageText(chat_id=orig_chat_id, message_id=orig_message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)


def admin_mention(update, context):
    bot = context.bot
    if update.message.chat.username is None:
        return

    # for admin in admins:
    bot.sendMessage(config.admin_channel_id, text="*Someone needs an admin!*\n"
                                                  "\n*Chat:* {chat}"
                                                  "\n*Name:* {user}"
                                                  "\n\n[Direct Link](https://t.me/{g_name}/{m_id})".format(chat=update.message.chat.title,
                                                                                                           user=update.message.from_user.first_name,
                                                                                                           g_name=update.message.chat.username,
                                                                                                           m_id=update.message.message_id),
                    parse_mode="Markdown")


def flood_check(update, context):
    chat_id = update.effective_message.chat_id
    user_id = update.effective_message.from_user.id
    bot = context.bot
    floodBuffer.add_message(update.effective_message)
    if floodBuffer.flood_reached(user_id):
        log_msg = "Detected flood in chat @{} by user '{}'. Kicking user!".format(update.effective_message.chat.username, update.effective_message.from_user.full_name)
        notify_admins(log_msg)
        logger.info(log_msg)
        try:
            bot.kickChatMember(chat_id, user_id)
        except BadRequest:
            warn_msg = "User might be an admin, or something else went wrong while kicking!"
            logger.warning(warn_msg)
            notify_admins(warn_msg)


dp.add_handler(MessageHandler(Filters.group & (~ ScamFilters.allowedChatsFilter), leave_group))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.userJoinedFilter, check_and_ban_suspicious_users))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.channelForwardFilter, scam_detected))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.joinChatLinkFilter, scam_detected))
dp.add_handler(MessageHandler(Filters.group & AdminFilters.adminMentionFilter, admin_mention))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.usernameFilter, ask_admins))
dp.add_handler(MessageHandler(Filters.group & ScamFilters.tDotMeUsernameFilter, ask_admins))
dp.add_handler(MessageHandler(Filters.group, flood_check))
dp.add_handler(CallbackQueryHandler(callback_handler))

reload_admins()
updater.start_polling()
logger.info("Bot started as @{}".format(updater.bot.username))
updater.bot.sendMessage(config.admin_channel_id, text="Bot restarted")
logger.info("Admins are: {}".format(config.admins))
updater.idle()
