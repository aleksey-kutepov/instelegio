import asyncio
import logging
import os

from telegram import ReactionTypeEmoji, Update
from telegram.constants import ReactionEmoji
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)
instagram_url_start = "https://www.instagram.com/"


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        print(f"[stdout]\n{stdout.decode()}")
    if stderr:
        print(f"[stderr]\n{stderr.decode()}")


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


async def extract_instagram_vide(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Reply with video thumbnal"""
    if instagram_url_start in update.message.text:
        filename = "/tmp/test.mp4"
        await update.get_bot().set_message_reaction(
            update.message.chat_id,
            update.message.message_id,
            [ReactionTypeEmoji(ReactionEmoji.EYES)],
        )
        try:
            await run(
                f"yt-dlp -v -f mp4 -o {filename} {extract_link(update.message.text)}"
            )
            await update.message.reply_video(filename)
            await update.get_bot().set_message_reaction(
                update.message.chat_id,
                update.message.message_id,
                [ReactionTypeEmoji(ReactionEmoji.FIRE)],
            )
            os.remove(filename)
        except Exception:
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
        MessageHandler(filters.TEXT & ~filters.COMMAND, extract_instagram_vide)
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
