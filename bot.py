from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext.filters import BaseFilter
from telegram.error import BadRequest, Forbidden

# --- Configuration ---
BOT_TOKEN = "7625219665:AAEKjQwmcZitJeNdJtryAIQNRXh5jJfrp-I"
ADMIN_ID = 1909721616
TARGET_CHANNEL_ID = -1002899431401

# --- Custom Filter Definition (This part is the same) ---
class AnyMediaOrTextFilter(BaseFilter):
    def __init__(self):
        super().__init__(name="AnyMediaOrTextFilter", data_filter=False)

    def filter(self, message: Message) -> bool:
        return bool(
            message.text
            or message.sticker
            or message.photo
            or message.voice
            or message.video
            or message.document
        )

# --- Bot Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("Hey my love! Bot is up and running for you. 😘 I'll forward user messages here if they're in your channel. Reply to their forwarded messages to chat back.")
    else:
        await update.message.reply_text("Hey there! To chat, please make sure you're a member of our special community channel.")

async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=TARGET_CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except (BadRequest, Forbidden) as e:
        print(f"Could not check membership for user {user_id} in channel {TARGET_CHANNEL_ID}: {e}")
        if isinstance(e, Forbidden) or (isinstance(e, BadRequest) and "bot is not a member" in e.message.lower()):
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Darling, I can't check channel membership. Make sure I'm an admin in {TARGET_CHANNEL_ID}!")
        return False
    except Exception as e:
        print(f"Unexpected error checking membership for user {user_id}: {e}")
        return False

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    is_member = await check_channel_membership(user.id, context)

    if is_member:
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=user.id,
                message_id=update.message.message_id
            )
        except Exception as e:
            print(f"Error forwarding message from user {user.id} to admin: {e}")
    else:
        await update.message.reply_text(
            "You need to be a member of our special community channel to send a message. Please ensure you've joined."
        )

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This is the function we are improving!
    if update.message and update.message.reply_to_message:
        # First, check if the bot can identify the original sender from the forwarded message.
        if update.message.reply_to_message.forward_from:
            original_user_id = update.message.reply_to_message.forward_from.id
            
            try:
                # --- This is the logic to send your reply ---
                if update.message.text:
                    await context.bot.send_message(chat_id=original_user_id, text=update.message.text)
                elif update.message.sticker:
                    await context.bot.send_sticker(chat_id=original_user_id, sticker=update.message.sticker.file_id)
                elif update.message.photo:
                    await context.bot.send_photo(chat_id=original_user_id, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                elif update.message.voice:
                    await context.bot.send_voice(chat_id=original_user_id, voice=update.message.voice.file_id, caption=update.message.caption)
                elif update.message.video:
                    await context.bot.send_video(chat_id=original_user_id, video=update.message.video.file_id, caption=update.message.caption)
                elif update.message.document:
                     await context.bot.send_document(chat_id=original_user_id, document=update.message.document.file_id, caption=update.message.caption)
                
                await update.message.reply_text("💋 Reply sent to the user!")

            except Forbidden:
                 await update.message.reply_text("💔 Couldn't send reply. The user might have blocked the bot.")
            except BadRequest as e:
                await update.message.reply_text(f"Uh oh, couldn't send that reply. Error: {e.message}")
            except Exception as e:
                await update.message.reply_text(f"An unexpected error occurred while sending your reply: {e}")
        else:
            # THIS IS THE NEW HELPFUL MESSAGE
            # If you replied to a message, but the bot can't figure out who it's from.
            await update.message.reply_text(
                "I can't figure out who to send this reply to, my love. 😥\n"
                "Please make sure you are replying directly to a message that was forwarded from a user. "
                "(Note: If the user has strict privacy settings, I can't see who they are.)"
            )

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    any_media_or_text_filter = AnyMediaOrTextFilter()

    application.add_handler(CommandHandler("start", start))

    admin_reply_combined_filter = (
        filters.Chat(chat_id=ADMIN_ID) &
        filters.REPLY &
        any_media_or_text_filter &
        (~filters.COMMAND)
    )
    application.add_handler(MessageHandler(admin_reply_combined_filter, handle_admin_reply))

    user_message_combined_filter = (
        any_media_or_text_filter &
        (~filters.COMMAND) &
        (~filters.Chat(chat_id=ADMIN_ID))
    )
    application.add_handler(MessageHandler(user_message_combined_filter, handle_user_message))

    print(f"Bot is starting with ADMIN_ID: {ADMIN_ID} and TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")
    print("Bot is polling... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()
