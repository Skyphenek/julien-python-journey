def print_board(board):
    for i, row in enumerate(board):
        row_str = " "
        for j, value in enumerate(row):
            row_str += value
            if j != len(row) - 1:
                row_str += " | "
        print(row_str)
        if i != len(board) - 1:
            print("-----------")

def get_move(turn, board):
    while True:
        print()
        print("Turn:", turn)
        row = int(input("Row (1-3): "))
        col = int(input("Column (1-3): "))

        if row < 1 or row > len(board):
            print("Invalid row. Please try again.")
            continue
        elif col < 1 or col > len(board[row - 1]):
            print("Invalid column. Please try again.")
            continue
        elif board[row - 1][col - 1] != " ":
            print("Cell already taken. Please try again.")
            continue
        else:
            break
    board[row - 1][col - 1] = turn

def check_win(board, turn):
    lines = [[(0,0), (0,1), (0,2)],
             [(1,0), (1,1), (1,2)],
             [(2,0), (2,1), (2,2)],
             [(0,0), (1,0), (2,0)],
             [(0,1), (1,1), (2,1)],
             [(0,2), (1,2), (2,2)],
             [(0,0), (1,1), (2,2)],
             [(0,2), (1,1), (2,0)]
    ]
    for line in lines:
        win = True
        for pos in line:
            row, col = pos
            if board[row][col] != turn:
                win = False
                break
        if win:
            print("Player", turn, "wins!")
            return True
    return False

board = [
    [" ", " ", " "],
    [" ", " ", " "],    
    [" ", " ", " "]
]

turn = "X"
turn_count = 0
print_board(board)

while turn_count < 9:
    print("It is your turn, " + turn)
    get_move(turn, board)
    print_board(board)
    winner = check_win(board, turn)
    if winner:
        break
    if turn == "X":
        turn = "O"
    else:
        turn = "X"
    turn_count += 1

if turn_count == 9 and not winner:
    print("Tied game! No one wins!")
else:
    print("The winner was", turn)