import json

def add_people():
    name = input("Name: ")
    age = input("Age: ")
    email = input("Email: ")

    person = {
            "name": name,
            "age": age,
            "email": email
    }
    return person

def display_people(people):
    for i, person in enumerate(people):
        print(i + 1, "-", person["name"], "|", person["age"], "|", person["email"])

def delete_contact(people):
    display_people(people)

    while True: 
        numbers = input("Enter the numbers of the contacts you want to delete (comma-separated): ")   
        try:
            number = int(numbers)
            if number < 1 or number > len(people):
                print("Invalid number. Please try again.")
            else:
                break
        except:
            print("Invalid input. Please enter a valid number.")

    people.pop(number - 1)
    print("Contact deleted successfully!")

def search_contact(people):
    display_people(people)
    search_name = input("Search for a contact by name: ").lower()
    found_contacts = []
    for person in people:
        if search_name in person["name"].lower():
            found_contacts.append(person)

    if found_contacts:
        print()
        print("Found contacts:")
        display_people(found_contacts)
    else:
        print("No contacts found.")

print("Hi, welcome to the people manager!")
print()

with open("contacts.json", "r") as f:
    people = json.load(f)["contacts"]


while True:
    print() 
    print("Contact list size:", len(people))
    command = input("You can 'add', 'delete', 'search' or 'q' to quit: ").lower()

    if command == "add":
        person = add_people()
        people.append(person)
        print("Person added successfully!")
    elif command == "delete":
        delete_contact(people)
    elif command == "search":
        search_contact(people)
    elif command == "q":
        print("Exiting the program...")
        break
    else:
        print("Invalid command. Please try again.")

with open("contacts.json", "w") as f:
    json.dump({"contacts": people}, f)

print(people) 