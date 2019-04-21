from datetime import date
from functools import wraps
from heapq import nlargest

from telegram import ChatAction, KeyboardButton, ReplyKeyboardMarkup, ParseMode

from database import MAIN_MONGO
from settings import TELEGRAM_BOT_AUTH_CODE, TOP_MOST_ACCESSED_URIS


# secure bot from Unauthorized access
def restricted_decorator(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        # user_id = update.effective_user.id
        telegram_data = MAIN_MONGO.get_telegram_data_from_db()

        if telegram_data is not None:
            if update.effective_user.id in telegram_data['ids']:
                # print("Unauthorized access denied for {}.".format(user_id))
                return func(update, context, *args, **kwargs)

        update.message.reply_text("Unauthorized access denied")
        return None

    return wrapped


def send_typing_action_decorator(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


@send_typing_action_decorator
def start(update, context):
    # print(context)
    # print(context.args)

    update.message.reply_text(f"Hey, {update.message.from_user.first_name}, please authorize!")


def send_stats_on_schedule(context):
    text_message = gather_statistics_from_db()

    if text_message:
        for user_id in MAIN_MONGO.get_telegram_data_from_db().get('ids', None):
            context.bot.send_message(chat_id=user_id,
                                     text=text_message,
                                     parse_mode=ParseMode.HTML)




@send_typing_action_decorator
def auth_command(update, context):
    telegram_data = MAIN_MONGO.get_telegram_data_from_db()

    if telegram_data is not None:
        if update.effective_user.id in telegram_data['ids']:
            context.bot.send_animation(update.message.chat_id,
                                       'https://media.tenor.com/videos/3ee8a323ada0cf64981db3fff949d4a3/mp4')
            update.message.reply_text("You are already authorized")
            return None
    if context.args:
        if context.args[0] == TELEGRAM_BOT_AUTH_CODE:
            MAIN_MONGO.write_telegram_user_to_db(update.effective_user.id)

            custom_keyboard = [
                [KeyboardButton(text="/stats")]
            ]
            reply_markup_general = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            context.bot.send_animation(update.message.chat_id,
                                       'https://media.tenor.com/videos/a06cb0f71bb7946e8a145cea6dcf48b8/mp4')
            update.message.reply_text(
                f"Congrats, {update.message.from_user.first_name}, now you're authorized to use my service!",
                reply_markup=reply_markup_general)
            return None

    update.message.reply_text("Incorrect auth code")


@send_typing_action_decorator
@restricted_decorator
def send_statistics(update, context):
    text_message = gather_statistics_from_db()

    if text_message:
        update.message.reply_text(
            text_message,
            parse_mode=ParseMode.HTML)
        return None
    update.message.reply_text(
        'Nothing to be sent')


def gather_statistics_from_db():
    today = date.today()

    data = MAIN_MONGO.get_stat_data_from_db(today.strftime("%d_%m_%y"))

    if data is not None:
        data.pop('_id')
        text_message = f'<b>Here is top opened URIs for today {today}:</b>\n'
        for index in nlargest(TOP_MOST_ACCESSED_URIS, data, key=data.get):
            text_message += f'<b>URI</b> - <i>{index}</i>  were accessed <b>{data.get(index)}</b> times\n'
        return text_message
    return False
