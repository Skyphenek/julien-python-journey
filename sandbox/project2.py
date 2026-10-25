
def get_number(number):
    while True:
            opertand = input("Number " + str(number) + ": ")
            try:
                return float(opertand)
            except:
                print("Invalid input. Please enter a valid number.")

operand = get_number(1)
operand2 = get_number(2)
sign = input("Sign: ")

if sign == "+":
    result = operand + operand2
elif sign == "-":
    result = operand - operand2
elif sign == "*":
    result = operand * operand2 
elif sign == "/":
    if float(operand2) != 0:
        result = operand / operand2
    else:
        print("Error: Division by zero")

print(result)
