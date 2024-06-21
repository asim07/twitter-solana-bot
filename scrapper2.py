import asyncio
from datetime import datetime
import json
import os
import random
import sys
import time

import regex as re
from twikit.twikit_async import Client

##############################################################################

TWITTER_ACCOUNTS = []

##############################################################################


def load_twitter_accounts_from_file(file_path):
    """
    Load Twitter accounts from a JSON file.
    """
    try:
        with open(file_path, 'r') as file:
            accounts = json.load(file)
            if not isinstance(accounts, list):
                raise ValueError("The JSON file should contain a list of account objects.")
            for account in accounts:
                if not all(key in account for key in ("username", "email", "password")):
                    raise ValueError("Each account object must contain 'username', 'email', and 'password' keys.")
            return accounts
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        print(f"Error loading accounts from file: {e}")
        sys.exit(1)


async def get_latest_tweet(twitter_user):
    """
    Asynchronously check for new tweets from the given username.
    """
    user_tweets = await twitter_user.get_tweets("Tweets")
    return user_tweets[0].text


def parse_solana_address(text):
    pattern = r"\b[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{32,44}\b"
    addresses = re.findall(pattern, text)
    return addresses[0] if addresses else None


async def login_to_twitter_accounts():
    twitter_users = []
    for idx, account in enumerate(TWITTER_ACCOUNTS):
        try:
            twitter_client = Client("en-US")
            await twitter_client.login(
                auth_info_1=account["username"], auth_info_2=account["email"], password=account["password"]
            )
            print(f"Logged in with account_{idx+1} successfully!")
            twitter_users.append((f"account_{idx+1}", twitter_client))
        except Exception as e:
            print(f"Failed to login with account_{idx+1}: {e}")
    if len(twitter_users) < 5:
        print("Failed to login with >= 5 Twitter accounts.")
        sys.exit(1)
    return twitter_users


async def check_for_tweets(usernames_to_check, twitter_users):
    last_known_tweet = {}

    try:
        while True:
            for account_num, twitter_client in twitter_users:
                for username_to_check in usernames_to_check:
                    try:
                        twitter_user = await twitter_client.get_user_by_screen_name(username_to_check)
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        latest_tweet = await get_latest_tweet(twitter_user)
                        if username_to_check not in last_known_tweet or latest_tweet != last_known_tweet[username_to_check]:
                            last_known_tweet[username_to_check] = latest_tweet
                            print(
                                f"{now} - New tweet from {username_to_check} fetched by {account_num} at https://twitter.com/{username_to_check}:\n\n {latest_tweet}"
                            )
                            sol_address = parse_solana_address(f"{latest_tweet}")
                            if sol_address:
                                print(f"{now} - Solana address found in tweet by {account_num}: {sol_address}")
                            else:
                                print(f"{now} - No Solana address found in tweet by {account_num}.")
                        else:
                            print(
                                f"{now} - No new tweets from {username_to_check} by {account_num}, sleeping 1s..."
                            )
                    except Exception as e:
                        print(f"{now} - An error occurred in {account_num}: {e}, sleeping 1s...")
                    finally:
                        await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Exiting due to KeyboardInterrupt...")


async def main(usernames_to_check, accounts_file):
    try:
        global TWITTER_ACCOUNTS
        TWITTER_ACCOUNTS = load_twitter_accounts_from_file(accounts_file)
        twitter_users = await login_to_twitter_accounts()
        await check_for_tweets(usernames_to_check, twitter_users)
    except IndexError:
        print("Please provide at least one Twitter username to check for new tweets.\n")
        print("Example: python check_for_tweets.py account1 account2\n")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Please provide the path to the accounts file and at least one Twitter username to check for new tweets.\n")
        print("Example: python check_for_tweets.py twitter_accounts.json account1 account2\n")
        sys.exit(1)
    accounts_file = sys.argv[1]
    usernames = sys.argv[2:]
    asyncio.run(main(usernames, accounts_file))
