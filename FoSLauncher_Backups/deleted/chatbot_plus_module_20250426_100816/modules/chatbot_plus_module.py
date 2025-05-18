# chatbot_plus_module.py

"""
FoSGamers Chatbot+ MVP
A minimal working version of the Chatbot+ app integrated into FoSLauncher.
Handles basic input, command routing, and responses using static knowledge.
Can be expanded into real-time assistant or Twitch/YouTube integration in future updates.
"""

import time
import random

RESPONSES = {
    "hello": [
        "Hey there! Welcome to the FoSGamers Chatbot+.",
        "Hi! Ready to crack some booster packs?",
        "Greetings, wanderer of the Wasteland!"
    ],
    "help": [
        "You can say things like 'open booster', 'show inventory', or 'run event'.",
        "Commands include: open pack, roll dice, give loot."
    ],
    "open booster": [
        "Cracking a booster... You pulled a Mythic Rare!",
        "Opening... Looks like you got a foil rare and a token."  
    ],
    "roll dice": [
        "You rolled a d20: {roll}",
        "Dice roll result: {roll}"
    ]
}

def chatbot_loop():
    print("\n[Chatbot+] Type 'exit' to leave the chatbot.")
    while True:
        user_input = input("You > ").strip().lower()
        if user_input == "exit":
            print("Goodbye!")
            break

        handled = False
        for trigger, replies in RESPONSES.items():
            if trigger in user_input:
                if "{roll}" in replies[0]:
                    roll = random.randint(1, 20)
                    print("Bot > " + random.choice(replies).format(roll=roll))
                else:
                    print("Bot > " + random.choice(replies))
                handled = True
                break

        if not handled:
            print("Bot > I'm not sure how to respond to that yet.")


if __name__ == "__main__":
    chatbot_loop()