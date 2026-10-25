nom = input("Entrez votre nom : ")
#âge = input("Entrez votre âge : ")
#ville = input("Entrez votre ville : ")
#pays = input("Entrez votre pays : ")
#langue = input("Entrez votre langue : ")

personne = {
    "nom": nom,
    #"âge": âge,
    #"ville": ville,
    #"pays": pays,
    #"langue": langue
}   

print("Hello", nom, "wanna play a game?")

should_we_play = input("Do you want to play? (yes/no): ").lower()

if should_we_play == "yes" or should_we_play == "y":
    print("Great! Let's play!")
    if nom.lower() == "julien":
        print("Julien! T'es un champion!")
    elif nom.lower() == "laetitia": 
        print("Allez ma Laetiti! T'es une championne!")
    else:
        print("Mais t'as aucune chance, bro! " + "You'd better go back to your mom's basement and play with your toys!🖕")
    weapon = input("Choose your weapon: sword or bow? (sword/bow): ").lower()
    direction = input("Do you want to go left or right? (left/right): ").lower()
    if direction == "left":
        choice = input("Okay, now you see a bridge. Do you want to cross it or swim under it? (cross/swim): ").lower()
        if choice == "cross":
            print("You crossed the bridge and found a treasure! You win!")
        elif choice == "swim"  and weapon == "sword":
            print("You swam under the bridge and killed a fish! You win!")
        elif choice == "swim":
            print("You swam under the bridge and got eaten by a fish! Game over!")
    else:  
        print("You went right and fell into a pit! Game over!")     
else:
    print("Loser! " + "Go back to mom's basement and play with your toys!🖕")


