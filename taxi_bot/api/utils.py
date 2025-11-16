"""
Utility functions for API operations
"""
import os
import logging
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)


def send_driver_notification(driver_telegram_id, notification_type, context_data=None):
    """Send notification to driver via Telegram bot"""
    try:
        from bot_service.driver.dictionary import translations
        from api.models import User
        
        # Get bot token
        bot_token = os.getenv('TG_BOT_TOKEN_DRIVER')
        if not bot_token:
            logger.error("Driver bot token not found")
            return False

        bot = Bot(token=bot_token)

        # Get driver language
        try:
            driver_user = User.objects.get(telegram_id=str(driver_telegram_id))
            language = driver_user.language
        except:
            language = 'kaz'

        # Prepare message based on notification type
        if notification_type == 'document_approved':
            document_type = context_data.get('document_type', 'Document')
            message = translations['document_approved'][language].format(
                document_type=document_type
            )
            # Send notification
            bot.send_message(
                chat_id=driver_telegram_id,
                text=message
            )
            logger.info(f"Sent {notification_type} notification to driver {driver_telegram_id}")
            return True
            
        elif notification_type == 'document_rejected':
            document_type = context_data.get('document_type', 'Document')
            message = translations['document_rejected'][language].format(
                document_type=document_type
            )
            # Send notification
            bot.send_message(
                chat_id=driver_telegram_id,
                text=message
            )
            logger.info(f"Sent {notification_type} notification to driver {driver_telegram_id}")
            return True
            
        elif notification_type == 'driver_verified':
            message = translations['driver_fully_verified'][language]
            
            # After verification, send main menu
            # Get driver to check online status
            from api.services import DriverService
            driver, _ = DriverService.get_or_create_driver(str(driver_telegram_id))
            
            # Build main menu keyboard
            if driver and driver.is_online:
                online_button = translations['buttons']['go_offline'][language]
            else:
                online_button = translations['buttons']['go_online'][language]
            
            keyboard = [
                [KeyboardButton(online_button)],
                [KeyboardButton(translations['buttons']['active_rides'][language])],
                [KeyboardButton(translations['buttons']['statistics'][language]),
                 KeyboardButton(translations['buttons']['history'][language])],
                [KeyboardButton(translations['buttons']['support'][language])],
                [KeyboardButton(translations['buttons']['settings'][language])]
            ]
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            # Send verification message
            bot.send_message(
                chat_id=driver_telegram_id,
                text=message
            )
            
            # Send main menu
            bot.send_message(
                chat_id=driver_telegram_id,
                text=translations['main_menu'][language],
                reply_markup=reply_markup
            )
            
            logger.info(f"Sent {notification_type} notification and main menu to driver {driver_telegram_id}")
            return True
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False

    except Exception as e:
        logger.error(f"Error sending {notification_type} notification to driver {driver_telegram_id}: {str(e)}")
        return False


def send_passenger_notification(passenger_telegram_id, notification_type, context_data=None):
    """Send notification to passenger via Telegram bot"""
    try:
        # Try to import passenger dictionary, fallback to driver dictionary
        try:
            from bot_service.passenger.dictionary import translations
        except ImportError:
            # If passenger dictionary doesn't exist, use driver dictionary
            from bot_service.driver.dictionary import translations
            
        from api.models import User
        
        # Get bot token - try passenger bot first, fallback to driver bot
        bot_token = os.getenv('TG_BOT_TOKEN_PASSENGER') or os.getenv('TG_BOT_TOKEN_DRIVER')
        if not bot_token:
            logger.error("No bot token found")
            return False

        bot = Bot(token=bot_token)

        # Get passenger language
        try:
            passenger_user = User.objects.get(telegram_id=str(passenger_telegram_id))
            language = passenger_user.language
        except:
            language = 'kaz'

        # Prepare message based on notification type
        if notification_type == 'no_drivers_available':
            message = translations['no_drivers_available'][language]
        else:
            message = f"Notification: {notification_type}"

        # Send notification
        bot.send_message(
            chat_id=passenger_telegram_id,
            text=message
        )

        logger.info(f"Sent {notification_type} notification to passenger {passenger_telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Error sending {notification_type} notification to passenger {passenger_telegram_id}: {str(e)}")
        return False
