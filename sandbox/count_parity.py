def count_parity(numbers):

    evens = odds = 0
    for number in numbers:
        if number % 2 == 0:
            evens += 1
        else:
            odds += 1
    return evens, odds
