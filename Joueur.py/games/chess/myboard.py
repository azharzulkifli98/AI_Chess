# here we will define same as before
# need to make fixes with check and stale mate
# then add the minimax function

import random
import copy
import datetime

convert = { "a":0, "b":1, "c":2, "d":3, "e":4, "f":5, "g":6, "h":7,
            0:"a", 1:"b", 2:"c", 3:"d", 4:"e", 5:"f", 6:"g", 7:"h" }

pointvalue = { "P":1, "B":3, "N":3, "R":5, "Q":9, "K":10,
            "p":-1, "b":-3, "n":-3, "r":-5, "q":-9, "k":-10 }

# helper functions for for getting all possible moves

def index_to_coords(oldy, oldx, newy, newx):
    return convert[oldx] + str(8 - oldy) + convert[newx] + str(8 - newy)

def coords_to_index(val):
    return ((8 - int(val[1])), convert[val[0]], (8 - int(val[3])), convert[val[2]])

def inbounds(y, x):
    return (x > -1 and x < 8 and y > -1 and y < 8)

def opposites(p1, p2):
    return (p1.isupper() and p2.islower()) or (p1.islower() and p2.isupper())



"""
This object will handle all chess mechanic functions
"""
class Board:
    # this will create any board based on the turn player using fen string
    def __init__(self, fen):
        self.matrix = []
        self.turn = "w"
        self.turnpieces = []
        self.enemypieces = []
        self.castling = "-"
        self.enpasse = "-"
        self.bk = [0, 0]
        self.wk = [0, 0]

        # need to break into pieces so that matrix can be built
        fixedfen = fen.replace(' ', '/')
        splitfen = fixedfen.split('/')
        for i in range(8):
            row = []
            val = str(splitfen[i])
            for j in val:
                if j.isnumeric():
                    for x in range(int(j)):
                        row.append(" ")
                else:
                    row.append(j)
            self.matrix.append(row)

        # need to set special move booleans
        self.turn = splitfen[8]
        self.castling = splitfen[9]
        self.enpasse = splitfen[10]

        # fill up the lists with remaining pieces for later use
        for i in range(8):
            for j in range(8):
                val = self.matrix[i][j]
                if val != " ":
                    if val == "k":
                        self.bk = [i, j]
                    elif val == "K":
                        self.wk = [i, j]
                    if self.turn == "w" and val.isupper() or self.turn == "b" and val.islower():
                        self.turnpieces.append([val, i, j])
                    elif self.turn == "w" and val.islower() or self.turn == "b" and val.isupper():
                        self.enemypieces.append([val, i, j])


    # define each piece with a signature move function
    # pawn and king will have special moves that can target multiple spaces
    # ex e4e5 becomes Pe4e5 or pe4e5 for en passe and ka1a2 or Ka1a2 for castle

    def pawn_moves(self, piece, y, x):
        moves = []
        # consider: firstturn, diagonals, enpasse, promotions
        if piece == "P":
            dir = -1
            home = 6
        else:
            dir = 1
            home = 1

        # advance
        if inbounds(y + dir, x) and self.matrix[y + dir][x] == " ":
            moves.append(index_to_coords(y, x, y + dir, x))
            # only possible if first move is too
            if inbounds(y + 2*dir, x) and self.matrix[y + 2*dir][x] == " " and y == home:
                moves.append(index_to_coords(y, x, y + 2*dir, x))

        # attack
        if inbounds(y + dir, x + 1):
            if opposites(piece, self.matrix[y + dir][x + 1]):
                moves.append(index_to_coords(y, x, y+dir, x+1))
            # subtract because algebra notation
            if self.enpasse == convert[x+1] + str(8 - y-dir):
                moves.append(piece + index_to_coords(y, x, y+dir, x+1))
        if inbounds(y + dir, x - 1):
            if opposites(piece, self.matrix[y + dir][x - 1]):
                moves.append(index_to_coords(y, x, y+dir, x-1))
            if self.enpasse == convert[x-1] + str(8 - y-dir):
                moves.append(piece + index_to_coords(y, x, y+dir, x-1))

        return moves


    def rook_moves(self, piece, y, x):
        moves = []
        for dir in [(1, 0), (0, 1), (0, -1), (-1, 0)]:
            cx = x + dir[1]
            cy = y + dir[0]
            if inbounds(cy, cx) and self.matrix[cy][cx] == " ":
                # all spaces between rook and next piece are valid
                while inbounds(cy, cx) and self.matrix[cy][cx] == " ":
                    moves.append(index_to_coords(y, x, cy, cx))
                    cx = cx + dir[1]
                    cy = cy + dir[0]
            # can also take piece if it belongs to enemy
            if inbounds(cy, cx) and opposites(piece, self.matrix[cy][cx]):
                moves.append(index_to_coords(y, x, cy, cx))
        return moves


    def knight_moves(self, piece, y, x):
        # better to use for loop over if statements
        moves = []
        for dir in [(-2, -1), (-2, 1), (-1, 2), (-1, -2), (1, 2), (1, -2), (2, 1), (2, -1)]:
            cx = x + dir[1]
            cy = y + dir[0]
            if inbounds(cy, cx):
                if self.matrix[cy][cx] == " " or opposites(piece, self.matrix[cy][cx]):
                    moves.append(index_to_coords(y, x, cy, cx))
        return moves


    def bishop_moves(self, piece, y, x):
        moves = []
        # same as rook but with diagonals
        for dir in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            cx = x + dir[1]
            cy = y + dir[0]
            if inbounds(cy, cx) and self.matrix[cy][cx] == " ":
                while inbounds(cy, cx) and self.matrix[cy][cx] == " ":
                    moves.append(index_to_coords(y, x, cy, cx))
                    cx = cx + dir[1]
                    cy = cy + dir[0]
            # can also take piece if it belongs to enemy
            if inbounds(cy, cx) and opposites(piece, self.matrix[cy][cx]):
                moves.append(index_to_coords(y, x, cy, cx))
        return moves


    def queen_moves(self, piece, y, x):
        # very simple
        moves = []
        moves = moves + self.bishop_moves(piece, y, x) + self.rook_moves(piece, y, x)
        return moves


    def king_moves(self, piece, y, x):
        # same as knight with addition of castling
        moves = []
        for dir in [(0, -1), (0, 1), (-1, 0), (1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            cx = x + dir[1]
            cy = y + dir[0]
            if inbounds(cy, cx):
                if self.matrix[cy][cx] == " " or opposites(piece, self.matrix[cy][cx]):
                    moves.append(index_to_coords(y, x, cy, cx))

        # neither king nor rook can move
        # cant use to get out of check
        # cant go over spaces being attacked or being occupied
        if self.is_in_check():
            pass
        elif piece.isupper():
            if "K" in self.castling:
                ready = 0
                for space in [[7, 5], [7, 6]]:
                    if self.matrix[space[0]][space[1]] == " " and not self.is_attacked(space[0], space[1]):
                        ready = ready + 1
                if ready == 2:
                    moves.append("Ke1g1")
                    self.castling = self.castling.replace("K", "")
            if "Q" in self.castling:
                ready = 0
                for space in [[7, 2], [7, 3]]:
                    if self.matrix[space[0]][space[1]] == " " and not self.is_attacked(space[0], space[1]):
                        ready = ready + 1
                if ready == 2:
                    moves.append("Qe1c1")
                    self.castling = self.castling.replace("Q", "")
        elif piece.islower():
            if "k" in self.castling:
                ready = 0
                for space in [[0, 5], [0, 6]]:
                    if self.matrix[space[0]][space[1]] == " " and not self.is_attacked(space[0], space[1]):
                        ready = ready + 1
                if ready == 2:
                    moves.append("ke8g8")
                    self.castling = self.castling.replace("k", "")
            if "q" in self.castling:
                ready = 0
                for space in [[0, 2], [0, 3]]:
                    if self.matrix[space[0]][space[1]] == " " and not self.is_attacked(space[0], space[1]):
                        ready = ready + 1
                if ready == 2:
                    moves.append("qe8c8")
                    self.castling = self.castling.replace("q", "")

        return moves


    def is_attacked(self, y, x):
        piece = self.matrix[y][x]

        # use backup is testing for empty spaces
        if piece == " ":
            if self.turn == "w":
                piece = "W"
            elif self.turn == "b":
                piece = "b"

        #pawn attacks
        if piece.islower():
            if inbounds(y+1, x+1) and self.matrix[y+1][x+1] == "P":
                return True
            elif inbounds(y+1, x-1) and self.matrix[y+1][x-1] == "P":
                return True
        else:
            if inbounds(y-1, x+1) and self.matrix[y-1][x+1] == "p":
                return True
            elif inbounds(y-1, x-1) and self.matrix[y-1][x-1] == "p":
                return True

        # knight attacks
        attacks = self.knight_moves(piece, y, x)
        for a in attacks:
            (oldy, oldx, newy, newx) = coords_to_index(a)
            if self.matrix[newy][newx] in "Nn" and opposites(piece, self.matrix[newy][newx]):
                return True

        # bishop/queen attacks
        attacks = self.bishop_moves(piece, y, x)
        for a in attacks:
            (oldy, oldx, newy, newx) = coords_to_index(a)
            if self.matrix[newy][newx] in "QqBb" and opposites(piece, self.matrix[newy][newx]):
                return True

        # rook/queen attacks
        attacks = self.rook_moves(piece, y, x)
        for a in attacks:
            (oldy, oldx, newy, newx) = coords_to_index(a)
            if self.matrix[newy][newx] in "QqRr" and opposites(piece, self.matrix[newy][newx]):
                return True

        # king attacks
        for a in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (-1, 1), (-1, -1)]:
            newy = y + a[0]
            newx = x + a[1]
            if inbounds(newy, newx):
                if self.matrix[newy][newx] in "Kk" and opposites(piece, self.matrix[newy][newx]):
                    return True

        # all places safe
        return False


    def is_in_check(self):
        if self.turn == "w":
            return self.is_attacked(self.wk[0], self.wk[1])
        else:
            return self.is_attacked(self.bk[0], self.bk[1])


    # for heuristic
    def update_pieces(self):
        self.turnpieces = []
        self.enemypieces = []
        for i in range(8):
            for j in range(8):
                val = self.matrix[i][j]
                if val != " ":
                    if self.turn == "w" and val.isupper() or self.turn == "b" and val.islower():
                        self.turnpieces.append([val, i, j])
                    elif self.turn == "w" and val.islower() or self.turn == "b" and val.isupper():
                        self.enemypieces.append([val, i, j])


    # will need for testing out moves ahead of time
    def move_piece(self, oldy, oldx, newy, newx):
        piece = self.matrix[oldy][oldx]

        self.matrix[oldy][oldx] = " "
        self.matrix[newy][newx] = piece

        if piece == "P":
            if newy == 0:
                self.matrix[newy][newx] = "Q"
            elif oldy - newy == 2:
                self.enpasse = str(convert[oldx]) + str(8 - newy + 1)
        elif piece == "p":
            if newy == 7:
                self.matrix[newy][newx] = "q"
            elif newy - oldy == 2:
                self.enpasse = str(convert[oldx]) + str(8 - newy - 1)

        if piece == "K":
            self.wk = [newy, newx]
        elif piece == "k":
            self.bk = [newy, newx]


    def print_matrix(self):
        for i in self.matrix:
            print(i)





"""
This object will hold board object and search algorithm functions
"""
class Minifish:
    def __init__(self, myboard):
        self.board = myboard


    def test_valid_move(self, move):
        # example e2e4 or Ke8c8
        copyboard = copy.deepcopy(self.board.matrix)
        copywk = self.board.wk
        copybk = self.board.bk

        # simulate move
        if len(move) > 4:
            if move[0] == "P" or move[0] == "p":
                # enpasse, need to remove other pawn
                (oldy, oldx, newy, newx) = coords_to_index(move[1:])
                self.board.move_piece(oldy, oldx, newy, newx)
                self.board.move_piece(oldy, oldx, oldy, newx)
            elif move[0] in "KQkq":
                # castling already set to be safe
                pass
        else:
            (oldy, oldx, newy, newx) = coords_to_index(move)
            self.board.move_piece(oldy, oldx, newy, newx)

        safe = not self.board.is_in_check()

        self.board.matrix = copy.deepcopy(copyboard)
        self.board.wk = copywk
        self.board.bk = copybk
        return safe


    def get_piece_valid_moves(self, piece, y, x):
        moves = []

        if piece == "P" or piece == "p":
            moves = self.board.pawn_moves(piece, y, x)

        elif piece == "N" or piece == "n":
            moves = self.board.knight_moves(piece, y, x)

        elif piece == "R" or piece == "r":
            moves = self.board.rook_moves(piece, y, x)

        elif piece == "B" or piece == "b":
            moves = self.board.bishop_moves(piece, y, x)

        elif piece == "Q" or piece == "q":
            moves = self.board.queen_moves(piece, y, x)

        elif piece == "K" or piece == "k":
            moves = self.board.king_moves(piece, y, x)

        # only get those that dont put king in check
        valid = []
        for move in moves:
            if self.test_valid_move(move) == True:
                valid.append(move)

        return valid



    def change_turn(self):
        if self.board.turn == "b":
            self.board.turn = "w"
        else:
            self.board.turn = "b"


    def get_all_moves(self):
        self.board.update_pieces()
        allpieces = self.board.turnpieces
        allmoves = []

        for p in allpieces:
            nextmove = self.get_piece_valid_moves(p[0], p[1], p[2])
            if nextmove != []:
                allmoves.append(nextmove)

        # format is [ [d3d4, d3d4, d3d4],  [f3f4, f3f4, f3f4],  [etc] ]
        return allmoves


    def is_in_checkmate(self):
        if self.board.is_in_check():
            moves = self.get_all_moves()
            if moves == []:
                # no escape
                return True
            else:
                # escape found
                return False
        else:
            return False


    # is independent of turn, positive is white balck is very very black
    def get_heuristic(self):
        self.board.update_pieces()
        score = 0

        if self.is_in_checkmate():
            if self.board.turn == "w":
                return -100
            else:
                return 100
        
        # generally want more pieces in center
        totalpieces = self.board.enemypieces + self.board.turnpieces
        for p in totalpieces:
            if p[1] == 3 or p[1] == 4:
                score = score + (pointvalue[p[0]] * 2)
            else:
                score = score + pointvalue[p[0]]

        # also consider pieces under attack
        for p in totalpieces:
            if self.board.is_attacked(p[1], p[2]):
                score = score + pointvalue[p[0]]

        return score



    def minimax(self, chessboard, curdepth, mymove):
        # first simulate move chosen
        if mymove != "":
            self.board = copy.deepcopy(chessboard)

            # forgot to check whether move was special or not
            if len(mymove) > 4:
                if mymove[0] == "P" or mymove[0] == "p":
                    # enpasse, need to remove other pawn
                    (oldy, oldx, newy, newx) = coords_to_index(mymove[1:])
                    self.board.move_piece(oldy, oldx, newy, newx)
                    self.board.move_piece(oldy, oldx, oldy, newx)
                elif mymove[0] in "KQkq":
                    # castling, move king and a rook
                    (oldy, oldx, newy, newx) = coords_to_index(mymove[1:])
                    self.board.move_piece(oldy, oldx, newy, newx)
                    if mymove[0] == "K":
                        self.board.move_piece(7, 7, 7, 5)
                    elif mymove[0] == "Q":
                        self.board.move_piece(7, 0, 7, 3)
                    elif mymove[0] == "k":
                        self.board.move_piece(0, 7, 0, 5)
                    elif mymove[0] == "q":
                        self.board.move_piece(0, 0, 0, 3)
            else:
                (oldy, oldx, newy, newx) = coords_to_index(mymove)
                self.board.move_piece(oldy, oldx, newy, newx)
            self.board.update_pieces()
            self.change_turn()


        # if terminal reached return given score and associated move
        if curdepth <= 0 or self.is_in_checkmate():
            score = self.get_heuristic()
            return (mymove, score)


        # if white/max turn then find biggest of the min
        elif self.board.turn == "w":
            bestscore = -100
            bestmove = ""
            allmoves = self.get_all_moves()
            for piece in allmoves:
                for move in piece:
                    possible = self.minimax(self.board, curdepth - 1, move)
                    # need reset after each move
                    self.board = copy.deepcopy(chessboard)

                    if bestscore < possible[1]:
                        bestmove = move
                        bestscore = possible[1]
                    #elif best[1] == possible[1] and random.getrandbits(1):
                    #    best = (move, possible[1])


        # if min/black then pick min of the maxes
        elif self.board.turn == "b":
            bestscore = 100
            bestmove = ""
            allmoves = self.get_all_moves()
            for piece in allmoves:
                for move in piece:
                    possible = self.minimax(self.board, curdepth - 1, move)
                    self.board = copy.deepcopy(chessboard)

                    if bestscore > possible[1]:
                        bestmove = move
                        bestscore = possible[1]
                    #elif best[1] == possible[1] and random.getrandbits(1):
                    #    best = (move, possible[1])
            
        return (bestmove, bestscore)




    def pick_move(self, totaltime):
        # first get total time usable
        usable = totaltime / 32

        bestmove = ""
        curtime = usable
        if totaltime > 300000:
            i = 2
        else:
            i = 1

        # then decide on depth and whether to go for a round        
        while curtime >= usable * 0.40:
            bestmove = self.minimax(self.board, i, "")
            i += 1
            curtime = update()

        # then return best move, dont forget to strip front letters first
        bestmove = bestmove[0]
        if len(bestmove) > 0 and bestmove[0] in "pPkKqQ":
            bestmove = bestmove[1:]
        return bestmove




    # just for testing correctness of board object
    def pick_random_move(self):
        if self.is_in_checkmate():
            return ""
        else:
            pieces = self.get_all_moves()
            i = random.randint(0, len(pieces) - 1)
            pick = pieces[i]
            i = random.randint(0, len(pick) - 1)
            move = pick[i]

            if move[0] in "pPkKqQ":
                move = move[1:]
            return move




# include some test cases

