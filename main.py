import configparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, ConversationHandler, CallbackQueryHandler, CommandHandler, CallbackContext
import jenkins
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Stages
DISPLAYJOBS, SET_ENV, SET_JIRA, PARAMETERS, TRIGGER_BUILD, CURRENT_BUILD_CANCEL_OPTION, CANCEL_BUILD = range(7)
# # Callback data
ONE, TWO, THREE, FOUR, FIVE, SIX = range(6)


def start(update: Update, context: CallbackContext):
    user = update.message.chat.username
    name = update.message.chat.first_name
    registeredUser = config.get('key', 'user')
    print(user)
    print(f'registeredUser===>>{registeredUser}')
    if user in registeredUser:
        text = """
                    Hello, I am Mr RoBot,
                    In case of any problem, Please send email to email.aloksrivastav@gmail.com\n
                    \n *****Welcome to the below Options*****\n
                    """

        keyboard = [
            [
                InlineKeyboardButton("Show me the Jobs", callback_data=str(ONE)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        update.message.reply_text(text, reply_markup=reply_markup)
        # Tell ConversationHandler that we're in state `FIRST` now
        return DISPLAYJOBS
    else:
        update.message.reply_text(f"Hi {name},\n you are not authorized to access this channel ")


def one(update: Update, context: CallbackContext) -> None:
    """Show new choice of buttons"""
    query = update.callback_query
    query.answer()
    global con
    con = jenkins.Jenkins(url='http://localhost:9090', username='admin', password='admin')
    # print(con.get_jobs())
    l1 = con.get_jobs()
    l2 = []
    for i in l1:
        l2.append(i['name'])
    key = []
    for i in l2:
        key.append([InlineKeyboardButton(i, callback_data=i)])
    print(key)
    keyboard = key
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text='Below are the Jobs', reply_markup=reply_markup)
    return SET_ENV


def two(update: Update, context: CallbackContext) -> None:
    """Show new choice of buttons"""
    query = update.callback_query
    global JobName
    JobName = query.data
    print(f'Job Name is {JobName}')
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("SIT", callback_data="SIT"),
            InlineKeyboardButton("PT", callback_data="PROD"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Lets First Choose the Environment First", reply_markup=reply_markup
    )
    return SET_JIRA


def three(update: Update, context: CallbackContext) -> None:
    """Show new choice of buttons"""
    query = update.callback_query
    global Env
    Env = query.data
    print(f'The Env is {Env}')
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("YES", callback_data="Yes"),
            InlineKeyboardButton("NO", callback_data="No"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Bug Logging in Jira", reply_markup=reply_markup)
    return PARAMETERS


def four(update: Update, context: CallbackContext) -> None:
    """Show new choice of buttons"""
    query = update.callback_query
    global JIRA_stats
    JIRA_stats = query.data
    text = (f'******Below are the configuration that you have selected :******\n'
            f'\nEnv ={Env} \n JIRA_TICKET = {JIRA_stats} \n JOB NAME = {JobName}\n'
            f'\n Please select from below options')
    global payload
    payload = {
        "ENV": Env,
        "Bug Logging in Jira": JIRA_stats
    }
    print(payload)
    keyboard = [
        [
            InlineKeyboardButton("Trigger build", callback_data="Trigger build"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=text, reply_markup=reply_markup)
    return TRIGGER_BUILD


def trigger_jenkins_build(payload, jobName):
    try:
        print("+++++++++++++++++++++++++++++++++++++\n")
        print(jobName)
        print(payload)
        print("++++++++++++++++++++++++++++++++++++++\n")
        status = con.build_job(name=jobName, parameters=payload)
        print(status)
        print(f'{jobName} is  triggered successfully')
        return True
    except Exception as e:
        print(f'{jobName} is not triggered successfully')
        print(e)
        return False


def five(update: Update, context: CallbackContext) -> None:
    """Show new choice of buttons"""
    query = update.callback_query
    print(query.data)
    if query.data == 'Trigger build':
        is_triggered = trigger_jenkins_build(payload=payload, jobName=JobName)
        print(f'is_triggered--->{is_triggered}')
        if is_triggered:
            bot = context.bot
            bot.send_message(chat_id=query.message.chat_id, message_id=query.message.message_id,
                             text="Build is triggered ")
            # update.message.reply_text("Build triggered successfully", reply_markup=reply_markup)
            keyboard = [
                [
                    InlineKeyboardButton("Cancel Build", callback_data="Cancel Build"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id=query.message.chat_id, text="Incase this Build is triggered incorrectly ",
                             reply_markup=reply_markup)
            return CURRENT_BUILD_CANCEL_OPTION
        else:
            print("Exception Occured")
            query.edit_message_text(text="Exception Occured")
            return ConversationHandler.END
    elif query.data == 'Cancel':
        print('This needs to be cancelled')
        query.edit_message_text(text="Please begin the chat again with Mr Robot and  this time choose carefully")
        return ConversationHandler.END
    else:
        print("Incorrect")


def six(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    print(query.data)
    keyboard = [
        [
            InlineKeyboardButton("Cancel build", callback_data="Trigger build"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Incase this Build is triggered incorrectly ", reply_markup=reply_markup)
    return CANCEL_BUILD


def return_current_build():
    currentbuildExecution = con.get_running_builds()
    for i in currentbuildExecution:
        i.get('number')
        return i.get('number')


def seven(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    buildnumber = return_current_build()
    bot = context.bot
    try:
        stopbuild = con.stop_build(name=JobName, number=buildnumber)
        bot.send_message(chat_id=query.message.chat_id,
                         text=f"Build {buildnumber} of {JobName} Job Succesfully stopped")
        return CANCEL_BUILD
    except Exception as E:
        print(E)
    return CANCEL_BUILD


def main():
    config.read('config.cfg')
    token = config.get('key', 'token')

    updater = Updater(token, use_context=True)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DISPLAYJOBS: [CallbackQueryHandler(one)],
            SET_ENV: [CallbackQueryHandler(two)],
            SET_JIRA: [CallbackQueryHandler(three)],
            PARAMETERS: [CallbackQueryHandler(four)],
            TRIGGER_BUILD: [CallbackQueryHandler(five)],
            CURRENT_BUILD_CANCEL_OPTION: [CallbackQueryHandler(six)],
            CANCEL_BUILD: [CallbackQueryHandler(seven)]

        },
        fallbacks=[CommandHandler('start', start)],
    )
    # Add ConversationHandler to dispatcher that will be used for handling
    # updates
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    main()
