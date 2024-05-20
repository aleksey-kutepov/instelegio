import asyncio
import logging
import os
import pyroscope

from telegram import ReactionTypeEmoji, Update
from telegram.constants import ReactionEmoji
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)
instagram_url_start = "https://www.instagram.com/"

addr = os.getenv("PYROSCOPE_SERVER_ADDRESS") or "http://pyroscope:4040"
logger.info("Pyroscope server is: ", addr)

pyroscope.configure(
    application_name="instelegio",
    server_address=addr,
    enable_logging=True,
)


async def runDownloader(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    logger.info(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        logger.info(f"[stdout]\n{stdout.decode()}")
    if stderr:
        logger.info(f"[stderr]\n{stderr.decode()}")


def extract_link(message: str) -> str:
    """Cut the IG link from the given string

    Args:
        message (str): # https://www.instagram.com/p/C5DoXclMbPn/?igsh=MWQ1ZGUxMzBkMA== example url

    Returns:
        str: https://www.instagram.com/p/C5DoXclMbPn/?igsh=MWQ1ZGUxMzBkMA==
    """
    start = message.find(instagram_url_start)
    t = message[start:]
    end = t.find(" ")
    link = t[:end]
    return link


async def extract_instagram_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Reply with video thumbnail"""
    if instagram_url_start in update.message.text:
        filename = "/tmp/test.mp4"
        with pyroscope.tag_wrapper({"function": "initial_reply"}):
            await update.get_bot().set_message_reaction(
                update.message.chat_id,
                update.message.message_id,
                [ReactionTypeEmoji(ReactionEmoji.EYES)],
            )
        try:
            with pyroscope.tag_wrapper({"function": "download_video"}):
                link = extract_link(update.message.text)
                await runDownloader(
                    f"yt-dlp -v -f mp4 -o {filename} {link}"
                )
            with pyroscope.tag_wrapper({"function": "upload_video"}):
                await update.message.reply_video(filename)
            await update.get_bot().set_message_reaction(
                update.message.chat_id,
                update.message.message_id,
                [ReactionTypeEmoji(ReactionEmoji.FIRE)],
            )
            with pyroscope.tag_wrapper({"function": "remove_video"}):
                os.remove(filename)
        except Exception as e:
            logger.error("Something went wrong: ", e)
            await update.get_bot().set_message_reaction(
                update.message.chat_id,
                update.message.message_id,
                [ReactionTypeEmoji(ReactionEmoji.CRYING_FACE)],
            )


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    telegram_token = os.environ.get("TOKEN", "")

    application = Application.builder().token(telegram_token).build()

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND,
                       extract_instagram_video)
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
