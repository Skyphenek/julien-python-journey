import random
def roll():
    min_value = 1
    max_value = 6
    roll = random.randint(min_value, max_value)

    return roll

while True:
    players = input("Enter the names of the players (comma-separated): ")
    if players.isdigit():
        players = int(players)
        if 2 <= players <= 4:
            break
        else:
            print("Invalid input. Please enter a number between 2 and 4.")
    else:
        print("Invalid input. Please enter a number between 2 and 4.")

print(players)

