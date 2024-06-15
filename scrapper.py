import asyncio
from datetime import datetime  # Import datetime for timestamps
import os
import random
import sys

import regex as re
import telebot
from telethon import TelegramClient
from twikit.twikit_async import Client

##############################################################################

TWITTER_USERNAME="chaudhryasi.m5@gmail.com"
TWITTER_EMAIL="chaudhryasi"
TWITTER_PASSWORD="11229117878"



TWITTER_USERNAME_2="chaudhr.ya.sim5@gmail.com"
TWITTER_EMAIL_2="ChTeasd64183"
TWITTER_PASSWORD_2="112291178Asd@"

TWITTER_USERNAME_3="chaudhrya.sim5@gmail.com"
TWITTER_EMAIL_3="cancda113293768"
TWITTER_PASSWORD_3="112291178Asd@"

TWITTER_USERNAME_4="chaud.hryasim5@gmail.com"
TWITTER_EMAIL_4="hryasim5"
TWITTER_PASSWORD_4="112291178Asd@"

TWITTER_USERNAME_5="ch.audhryasim5@gmail.com"
TWITTER_EMAIL_5="ch_teasd"
TWITTER_PASSWORD_5="112291178Asd@"

TWITTER_USERNAME_6="cha.udhryasim5@gmail.com"
TWITTER_EMAIL_6="udhryasim5"
TWITTER_PASSWORD_6="112291178Asd@"

##############################################################################


# telegram_alerts_bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))


async def get_latest_tweet(twitter_user):
    """
    Asynchronously check for new tweets from the given username.
    """

    # Get user tweets
    user_tweets = await twitter_user.get_tweets("Tweets")  # gets Tweets (Replies, Media, Likes also ok)
    return user_tweets[0].text


def parse_solana_address(text):
    # Regex pattern for a Solana address (32-44 characters)
    pattern = r"\b[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{32,44}\b"
    addresses = re.findall(pattern, text)
    return addresses[0] if addresses else None


async def check_for_tweets(username_to_check):

    # Initialize the Twitter and Telegram clients
    
    print("loading account 1")
    twitter_client_1 = Client("en-US")
    await twitter_client_1.login(auth_info_1=TWITTER_USERNAME, auth_info_2=TWITTER_EMAIL, password=TWITTER_PASSWORD)
    twitter_user_1 = await twitter_client_1.get_user_by_screen_name(username_to_check)

    print("loading account 2")

    twitter_client_2 = Client("en-US")
    await twitter_client_2.login(
        auth_info_1=TWITTER_USERNAME_2, auth_info_2=TWITTER_EMAIL_2, password=TWITTER_PASSWORD_2
    )
    twitter_user_2 = await twitter_client_2.get_user_by_screen_name(username_to_check)

    print("loading account 3")

    twitter_client_3 = Client("en-US")
    await twitter_client_3.login(
        auth_info_1=TWITTER_USERNAME_3, auth_info_2=TWITTER_EMAIL_3, password=TWITTER_PASSWORD_3
    )
    twitter_user_3 = await twitter_client_3.get_user_by_screen_name(username_to_check)

    print("loading account 4")

    twitter_client_4 = Client("en-US")
    await twitter_client_4.login(
        auth_info_1=TWITTER_USERNAME_4, auth_info_2=TWITTER_EMAIL_4, password=TWITTER_PASSWORD_4
    )
    twitter_user_4 = await twitter_client_4.get_user_by_screen_name(username_to_check)

    print("loading account 5")

    twitter_client_5 = Client("en-US")
    await twitter_client_5.login(
        auth_info_1=TWITTER_USERNAME_5, auth_info_2=TWITTER_EMAIL_5, password=TWITTER_PASSWORD_5
    )

    twitter_user_5 = await twitter_client_5.get_user_by_screen_name(username_to_check)



    # telethon_client = await TelegramClient("bot", TELEGRAM_API_ID, TELEGRAM_API_HASH).start(TELEGRAM_PHONE_NUMBER)

    twitter_users = [twitter_user_1, twitter_user_2, twitter_user_3,twitter_user_4,twitter_user_5]
    last_known_tweet = ""

    try:
        while True:
            for twitter_user in twitter_users:
                try:
                    randomized_sleep_amount = random.randint(1, 6)
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    latest_tweet = await get_latest_tweet(twitter_user)
                    # if last_known_tweet == "":
                    #     last_known_tweet = latest_tweet
                    #     print(f"{now} - Initial tweet from {username_to_check}: {latest_tweet}")
                    # elif latest_tweet != last_known_tweet:
                    if latest_tweet != last_known_tweet:  # uncomment to get alerts for every tweet
                        last_known_tweet = latest_tweet
                        print(
                            f"{now} - New tweet from {username_to_check} at https://twitter.com/{username_to_check}:\n\n {latest_tweet}"
                        )
                        # telegram_alerts_bot.send_message(
                        #     TELEGRAM_CHAT_ID,
                        #     f"New tweet from {username_to_check} at https://twitter.com/{username_to_check}:\n\n {latest_tweet}",
                        # )
                        # Check for Solana address in tweet
                        sol_address = parse_solana_address(f"{latest_tweet}")
                        if sol_address:
                            with open("sol_address.txt", "w") as file:
                                file.write(sol_address)
                            print(f"{now} - Solana address found in tweet: {sol_address}")
                            os._exit(1)
                            # await telethon_client.send_message("bonkbot_bot", sol_address)
                            # telegram_alerts_bot.send_message(TELEGRAM_CHAT_ID, f"{sol_address}")
                        else:
                            print(f"{now} - No Solana address found in tweet.")

                    else:
                        print(f"{now} - No new tweets from {username_to_check}, sleeping {randomized_sleep_amount}s...")
                except Exception as e:
                    print(f"{now} - An error occurred: {e}, sleeping {randomized_sleep_amount}s...")
                finally:
                    await asyncio.sleep(randomized_sleep_amount)
    except KeyboardInterrupt:
        print("Exiting due to KeyboardInterrupt...")
    finally:
        await telethon_client.disconnect()


async def main():
    try:
        username_to_check = sys.argv[1]
        await check_for_tweets(username_to_check)
    except IndexError:
        print("Please provide a Twitter username to check for new tweets.\n")
        print("Example: python check_for_tweets.py IGGYAZALEA\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())