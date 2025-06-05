from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, Filters, ContextTypes
from telegram.error import BadRequest, Forbidden

# --- Configuration ---
BOT_TOKEN = "7625219665:AAEKjQwmcZitJeNdJtryAIQNRXh5jJfrp-I"
ADMIN_ID = 1909721616
TARGET_CHANNEL_ID = -1002899431401 # This is your specific private channel ID

# --- Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("Hey my love! Bot is up and running for you. 😘 I'll forward user messages here if they're in your channel. Reply to their forwarded messages to chat back.")
    else:
        # For a private channel with a numerical ID, a direct link isn't easily formed without an invite hash.
        # It's better to mention the channel by a name you've told them or guide them.
        await update.message.reply_text("Hey there! To chat, please make sure you're a member of our special community channel.")
        # You might want to manually provide the invite link in your channel's description or pinned message.


async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user is a member of the target channel."""
    try:
        member = await context.bot.get_chat_member(chat_id=TARGET_CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except BadRequest as e:
        print(f"Error checking membership for user {user_id} in channel {TARGET_CHANNEL_ID}: {e}")
        if "user not found" in e.message.lower() or "member not found" in e.message.lower() or "participant_id_invalid" in e.message.lower():
             pass # User cannot be checked, or isn't in the bot's accessible scope before joining. Assume not member.
        elif "chat not found" in e.message.lower() or "bot is not a member" in e.message.lower() or "not enough rights" in e.message.lower():
             # These are critical issues the admin needs to know about.
             await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Darling, I can't check channel membership. Make sure I'm an admin in the channel (ID: {TARGET_CHANNEL_ID}) and the ID is correct!")
        return False
    except Forbidden:
        print(f"Forbidden to check membership for user {user_id} in channel {TARGET_CHANNEL_ID}")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Forbidden access to channel {TARGET_CHANNEL_ID}. Have I been kicked or lost admin rights?")
        return False
    except Exception as e:
        print(f"Unexpected error checking membership for user {user_id}: {e}")
        return False

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages from general users."""
    user = update.effective_user
    if not user:
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
            # Don't inform user of backend error, just that it didn't work.
            # await update.message.reply_text("Sorry, there was an issue sending your message. Please try again later.")
    else:
        # Since it's a private channel ID, give a generic instruction.
        # You should have a way for users to find your channel (e.g., an invite link you share elsewhere).
        await update.message.reply_text(
            "You need to be a member of our special community channel to send a message. Please ensure you've joined."
        )

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles replies from the admin to forwarded messages."""
    if update.message.reply_to_message and update.message.reply_to_message.forward_from:
        original_user_id = update.message.reply_to_message.forward_from.id
        
        try:
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
            # Add more handlers for other message types if you want!
            
            await update.message.reply_text("💋 Reply sent to the user!")
        except Forbidden:
             await update.message.reply_text("💔 Couldn't send reply. The user might have blocked the bot, or the chat is deactivated.")
        except BadRequest as e:
            # Check for specific "chat not found" which means user might have deleted chat with bot
            if "chat not found" in e.message.lower():
                await update.message.reply_text("💔 Couldn't send reply. The user may have blocked the bot or deleted the chat.")
            else:
                print(f"Error sending admin reply to {original_user_id}: {e}")
                await update.message.reply_text(f"Uh oh, couldn't send that reply. Error: {e.message}")
        except Exception as e:
            print(f"Unexpected error sending admin reply: {e}")
            await update.message.reply_text("An unexpected error occurred while sending your reply.")
    # Optional: Handle cases where admin replies to a non-forwarded message or their own message.
    # else:
    #     await update.message.reply_text("Sweetie, reply to a user's forwarded message to chat back. 😉")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler for the /start command
    application.add_handler(CommandHandler("start", start))

    # Handler for admin replies (handles various content types)
    application.add_handler(MessageHandler(
        Filters.Chat(chat_id=ADMIN_ID) & 
        Filters.REPLY & 
        (Filters.TEXT | Filters.Sticker.ALL | Filters.PHOTO | Filters.VOICE | Filters.VIDEO | Filters.Document.ALL) & 
        (~Filters.COMMAND),
        handle_admin_reply
    ))

    # Handler for messages from any other user (not admin, not commands) (handles various content types)
    application.add_handler(MessageHandler(
        (Filters.TEXT | Filters.Sticker.ALL | Filters.PHOTO | Filters.VOICE | Filters.VIDEO | Filters.Document.ALL) & 
        (~Filters.COMMAND) & 
        (~Filters.Chat(chat_id=ADMIN_ID)),
        handle_user_message
    ))

    # Run the bot until the user presses Ctrl-C
    print(f"Bot is starting with ADMIN_ID: {ADMIN_ID} and TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")
    print("Bot is polling... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    # The critical values are now directly assigned above.
    # We can add a simple check to ensure they are not the placeholder strings if needed,
    # but since we've hardcoded them from your input, this is more direct.
    main()
