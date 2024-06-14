def format_dict_as_message(details: dict, emoji: str, action: str) -> str:
    """
    Helper function to format dictionary details into a Telegram message with emojis.

    Parameters:
    - details: The dictionary containing the details to be included in the message.
    - emoji: The emoji to use in the message.
    - action: The action (Buy, Sell, Error) to include in the message.

    Returns:
    - A formatted string representing the Telegram message.
    """
    message_lines = [f"{emoji} {action} Notification {emoji}"]
    for key, value in details.items():
        message_lines.append(f"{key}: {value}")
    return "\n".join(message_lines)

def buy_notification(details: dict) -> str:
    """
    Generates a buy notification message with appropriate emoji.

    Parameters:
    - details: The dictionary containing the buy details.

    Returns:
    - A formatted buy notification message for Telegram.
    """
    return format_dict_as_message(details, emoji="🛒", action="Buy")

def new_liquidity_notification(details: dict) -> str:
    """
    Generates a buy notification message with appropriate emoji.

    Parameters:
    - details: The dictionary containing the buy details.

    Returns:
    - A formatted buy notification message for Telegram.
    """
    return format_dict_as_message(details, emoji="🎇", action="Pool Detection")

def sell_notification(details: dict) -> str:
    """
    Generates a sell notification message with appropriate emoji.

    Parameters:
    - details: The dictionary containing the sell details.

    Returns:
    - A formatted sell notification message for Telegram.
    """
    return format_dict_as_message(details, emoji="💰", action="Sell")

def error_notification(details: dict) -> str:
    """
    Generates an error notification message with appropriate emoji.

    Parameters:
    - details: The dictionary containing the error details.

    Returns:
    - A formatted error notification message for Telegram.
    """
    return format_dict_as_message(details, emoji="⚠️", action="Error")

# Example usage:
# buy_details = {"Product": "Laptop", "Price": "$1200", "Quantity": 2}
# sell_details = {"Product": "Smartphone", "Price": "$800", "Quantity": 1}
# error_details = {"Error": "Payment failed", "Attempt": 1}

# print(buy_notification(buy_details))
# print(sell_notification(sell_details))
# print(error_notification(error_details))