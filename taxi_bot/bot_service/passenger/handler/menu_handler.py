"""
Passenger Main Menu Handlers
Handles main menu button interactions for passengers
"""
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext

from api.services import PassengerService
from bot_service.passenger.dictionary import translations
from bot_service.passenger.menu import main_menu, confirmation_menu
from bot_service.passenger.states import (MAIN_MENU, PICKUP_ADDRESS, LOCATION_UPDATE,
    DESTINATION_ADDRESS, CONFIRM_RIDE)


def handle_main_menu(update: Update, context: CallbackContext) -> int:
    """Handle main menu button clicks"""
    language = context.user_data.get('language', 'kaz')
    telegram_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    # Handle different button clicks
    if user_input == translations['buttons']['new_order'][language]:
        return handle_new_order(update, context)
    elif user_input == translations['buttons']['history'][language]:
        return handle_history(update, context)
    elif user_input == translations['buttons']['settings'][language]:
        return handle_settings(update, context)
    elif user_input == translations['buttons']['support'][language]:
        return handle_support(update, context)
    else:
        # Unknown command
        update.message.reply_text(
            translations['unknown_command'][language],
            reply_markup=ReplyKeyboardRemove()
        )
        main_menu(update, context)
        return MAIN_MENU


def handle_new_order(update: Update, context: CallbackContext) -> int:
    """Handle new order button"""
    language = context.user_data.get('language', 'kaz')
    telegram_id = str(update.effective_user.id)

    print(f"[PASSENGER_LOG] {telegram_id} starting new order")

    update.message.reply_text(
        translations['enter_pickup_address'][language],
        reply_markup=ReplyKeyboardRemove()
    )

    print(f"[PASSENGER_LOG] {telegram_id} returning PICKUP_ADDRESS state")
    return PICKUP_ADDRESS


def handle_history(update: Update, context: CallbackContext) -> int:
    """Handle history button"""
    language = context.user_data.get('language', 'kaz')
    telegram_id = str(update.effective_user.id)

    # Get passenger rides
    rides = PassengerService.get_passenger_rides(telegram_id, limit=10)

    if rides:
        history_message = f"📋 {translations['ride_history'][language]}\n\n"
        for i, ride in enumerate(rides, 1):
            # Get status translation from dictionary
            status_translations = translations.get('ride_status', {})
            status_dict = status_translations.get(ride.status, {})
            status_text = status_dict.get(language, ride.status)

            history_message += f"{i}. {ride.created_at.strftime('%d.%m.%Y %H:%M')} - {status_text}\n"

        update.message.reply_text(history_message, reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(
            translations['no_rides'][language],
            reply_markup=ReplyKeyboardRemove()
        )

    main_menu(update, context)
    return MAIN_MENU


def handle_settings(update: Update, context: CallbackContext) -> int:
    """Handle settings button"""
    language = context.user_data.get('language', 'kaz')
    telegram_id = str(update.effective_user.id)

    # Get passenger info
    passenger = PassengerService.get_passenger_by_telegram_id(telegram_id)
    user = PassengerService.get_user_by_telegram_id(telegram_id)

    if passenger and user:
        settings_message = translations['passenger_settings'][language].format(
            name=user.full_name,
            phone=user.phone_number or 'Не указан',
            language=language.upper(),
            total_rides=passenger.total_rides,
            balance=passenger.balance,
            registration_date=passenger.created_at.strftime('%d.%m.%Y')
        )

        update.message.reply_text(settings_message, reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(
            translations['settings_error'][language],
            reply_markup=ReplyKeyboardRemove()
        )

    main_menu(update, context)
    return MAIN_MENU


def handle_support(update: Update, context: CallbackContext) -> int:
    """Handle support button"""
    language = context.user_data.get('language', 'kaz')

    support_message = translations['support_info'][language]

    update.message.reply_text(support_message, reply_markup=ReplyKeyboardRemove())

    main_menu(update, context)
    return MAIN_MENU


def handle_pickup_address(update: Update, context: CallbackContext) -> int:
    """Handle pickup address input"""
    from api.services import geocode_address
    
    language = context.user_data.get('language', 'kaz')
    telegram_id = str(update.effective_user.id)
    pickup_address = update.message.text.strip()

    if len(pickup_address) < 5:
        update.message.reply_text(
            translations['invalid_address'][language],
            reply_markup=ReplyKeyboardRemove()
        )
        return PICKUP_ADDRESS

    print(f"[PASSENGER_LOG] {telegram_id} processing pickup address: '{pickup_address}'")
    
    # Initialize ride_data if it doesn't exist
    if 'ride_data' not in context.user_data:
        context.user_data['ride_data'] = {}
    
    # Geocode address to get coordinates
    try:
        lat, lng = geocode_address(pickup_address)
        print(f"[PASSENGER_LOG] {telegram_id} geocoded pickup address to: {lat}, {lng}")
    except Exception as e:
        print(f"[PASSENGER_LOG] {telegram_id} geocoding error: {e}")
        # Use default coordinates if geocoding fails (Almaty center)
        lat, lng = 43.2220, 76.8512

    # Store pickup data in ride_data format
    context.user_data['ride_data']['pickup_address'] = pickup_address
    context.user_data['ride_data']['pickup_lat'] = lat
    context.user_data['ride_data']['pickup_lng'] = lng
    
    # Also store in old format for compatibility
    context.user_data['pickup_address'] = pickup_address
    context.user_data['pickup_lat'] = lat
    context.user_data['pickup_lng'] = lng

    # Ask for destination address (no location button)
    update.message.reply_text(
        translations['enter_destination'][language],
        reply_markup=ReplyKeyboardRemove()
    )

    return DESTINATION_ADDRESS


def handle_location_update(update: Update, context: CallbackContext) -> int:
    """Handle location update from user (legacy support - redirects to pickup address handler)"""
    # If user sends location, treat it as pickup address input
    # Convert location to text and process as address
    language = context.user_data.get('language', 'kaz')
    
    if update.message.location:
        # User sent location - convert to address format
        lat = update.message.location.latitude
        lng = update.message.location.longitude
        address = f"📍 Координаты: {lat:.6f}, {lng:.6f}"
        
        # Store location data
        if 'ride_data' not in context.user_data:
            context.user_data['ride_data'] = {}
        
        context.user_data['ride_data']['pickup_address'] = address
        context.user_data['ride_data']['pickup_lat'] = lat
        context.user_data['ride_data']['pickup_lng'] = lng
        
        context.user_data['pickup_address'] = address
        context.user_data['pickup_lat'] = lat
        context.user_data['pickup_lng'] = lng
        
        # Ask for destination
        update.message.reply_text(
            translations['enter_destination'][language],
            reply_markup=ReplyKeyboardRemove()
        )
        
        return DESTINATION_ADDRESS
    else:
        # If text is sent, treat as address and process
        return handle_pickup_address(update, context)


