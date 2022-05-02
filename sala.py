from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import sys
import traceback
from wordle_aux import *

class Game:
    def __init__(self, manager):
        words = getWords()
        self.words = manager.list([words])
        hidden = getSecretWord(self.words[0])
        self.secret = manager.list([hidden])
        self.matrix = manager.list([[[Square() for j in range(WORD_LENGTH)] for i in range(N_TRIES)]])
        self.n_guesses = Value('i', 0) 
        self.running = Value('i', 1) # 1 running
        self.winner = manager.list([""])
        self.lock = Lock()

    def get_secret(self):
        return self.secret[0]
    
    def get_matrix(self):
        return self.matrix[0]

    def is_running(self):
        return self.running.value == 1
    
    def get_winner(self):
        return self.winner[0]

    def set_winner(self, pid):
        self.winner[0] = pid

    def stop(self):
        self.running.value = 0
    
    def add_guess(self, guess):
        # Añade la fila coloreada a la matriz
        self.lock.acquire()
        answer = getColorsFromGuess(guess, self.get_secret()) # Devuelve los colores correspondientes al guess
        matrix = self.get_matrix()
        for j in range(WORD_LENGTH):
            matrix[self.n_guesses.value][j].letter = guess[j]
            matrix[self.n_guesses.value][j].color = answer[j]
        self.matrix[0] = matrix
        self.lock.release()

    def get_info(self):
        if self.get_winner() == "" and self.n_guesses.value < N_TRIES: # Comprobamos que la partida sigue en juego
            secret = ""
        else: # Solo mandamos la palabra secreta una vez terminada la partida
            secret = self.get_secret()
        info = { # Actualizamos la información del juego
            "matrix" : self.get_matrix(),
            "is_running" : self.running.value == 1,
            "winner" : self.get_winner(),
            "secret" : secret
        }
        return info


def player(pid, conn, game: Game):
    try:
        print(f"player {pid} : STARTED")
        conn.send((pid, game.get_info()))
        while game.is_running():
            command = ""
            while command != "next":
                command = conn.recv() # Recibe el guess del jugador
                if command != "next" and command != "quit":
                    guess_str = command
                    print(f"player {pid} : GUESS : {guess_str}")
                    game.add_guess(guess_str) # Añadimos el guess a la matriz
                    game.n_guesses.value += 1
                    if guess_str == game.get_secret(): # Si el guess coincide con la palabra secreta, hemos terminado
                        game.set_winner(pid)
                        game.stop()
                elif command == "quit" or game.n_guesses.value == N_TRIES: # Si los jugadores se quedan sin intentos, hemos terminado
                    game.stop()
            conn.send(game.get_info()) # Enviamos la información del juego actualizada
    except:
        traceback.print_exc()
        conn.close()
    finally:
        print(f"Game ended")
        if game.get_winner() != "":
            print(f"player {game.get_winner()} won the game")
        else:
            print(f"players ran out of tries")
        print(f"the secret word was {game.get_secret()}")
        game.stop()
        conn.close() # Cerramos el jugador


def main(ip_address, port):
    manager = Manager()
    try:
        with Listener((ip_address, port), authkey=b"secret password") as listener:
            pid = 0
            players = []
            game = Game(manager)
            while game.is_running():
                conn = listener.accept() # Escuchamos para añadir otro jugador (un jugador se puede unir en cualquier momento de la partida)
                print(f"connection {pid} : ACCEPTED")
                players.append(Process(target=player, args=(pid, conn, game)))
                players[pid].start()
                pid += 1
    except Exception as e:
        traceback.print_exc()

if __name__=="__main__":
    ip_address = "127.0.0.1" # localhost
    port = 6000 # Puerto para jugar la sala
    if len(sys.argv)>1:
        ip_address = sys.argv[1]
    if len(sys.argv)>2:
        port = int(sys.argv[2])
    main(ip_address, port)

"""
para jugar a WORDLE DISTRIBUIDO

ip de simba: 147.96.81.245

en simba: python3 sala.py 147.96.81.245 7124 (elegir un puerto cualquiera)
cada jugador en su propio ordenador: python3 player.py 147.96.81.245 7124 (elegir el mismo puerto que la sala)
"""
