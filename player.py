from multiprocessing.connection import Client
import sys
import time
import traceback
import pygame
from wordle_aux import *

FPS = 30

class Player:
    def __init__(self, pid):
        self.pid = pid
        self.guess = [Square(guess=True) for _ in range(WORD_LENGTH)] # Cada jugador tiene su propia fila


class Game:
    def __init__(self, pid):
        self.player = Player(pid)
        self.pid = pid
        self.words = getWords()
        self.error_msg = ""

    def update(self, gameinfo): # Actualizara con los datos de la sala
        self.matrix = gameinfo["matrix"]
        self.running = gameinfo["is_running"]
        self.winner = gameinfo["winner"]
        self.secret = gameinfo["secret"]

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False


class Display:
    def __init__(self, game: Game):
        pygame.init()
        self.game = game
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.screen.fill(WHITE)
        pygame.display.set_caption(f"Wordle Distribuido - Player {game.player.pid}")
        self.clock = pygame.time.Clock()
        self.j = 0 # Llevamos este índice para saber en que posición de la palabra estamos
        self.refresh()

    def analyze_events(self):
        events = []
        for event in pygame.event.get(): # Escuchamos los distintos eventos
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN: # Si se pulsa una tecla
                if event.key == pygame.K_BACKSPACE: # Si pulsamos la tecla de borrar, actualizamos la palabra del jugador
                    if self.j > 0:
                        self.game.player.guess[self.j-1].letter = None
                        self.j -= 1
                elif event.key == pygame.K_RETURN: # Si pulsamos la tecla de enter
                    guess_str = get_word_from_row(self.game.player.guess, self.j) # Transformamos la fila del jugador a una palabra en formato "String"
                    if self.j == WORD_LENGTH: # Comprobamos si la palabra tiene suficientes letras
                        if guess_str in self.game.words: # Comprobamos si la palabra está en el diccionario
                            print(guess_str)
                            events.append(guess_str) # Enivamos la palabra factible a la sala para introducir en la matriz común
                            self.j = 0
                            self.game.player.guess = resetRow(self.game.player.guess) # Vaciamos la fila del guess del jugador para prepararla para la siguiente palabra 
                            self.game.error_msg = ""
                            self.refresh()
                        else:
                            self.game.error_msg = f"{guess_str.upper()} not in dictionary" # Devolvemos el error correspondiente
                            self.refresh()
                    else:
                        self.game.error_msg = f"{guess_str.upper()} is not long enough" # Devolvemos el error correspondiente
                        self.refresh()
                else: # Si pulsamos cualquier otra tecla (una letra)
                    if self.j < WORD_LENGTH:
                        if event.unicode.isalpha():
                            self.game.player.guess[self.j].letter = event.unicode.lower()
                            self.j += 1
        return events

    def refresh(self): # Actualizamos lo que vemos en la pantalla
        draw_grid(self.screen, self.game.matrix) # Dibujamos la cuadricula principal
        draw_divider(self.screen) # Dibujamos la linea entre la cuadricula y la fila del guess local
        draw_guess_row(self.screen, self.game.player.guess) # Dibujamos la fila del guess local
        render_message(self.screen, self.game.error_msg) # Dibujamos el mensaje (si hay) al final de la pantalla
        pygame.display.update()

    def tick(self):
        self.clock.tick(FPS)


def main(ip_address, port):
    try:
        with Client((ip_address, port), authkey=b"secret password") as conn:
            pid, gameinfo = conn.recv()
            print(f"---- player {pid} ----")
            game = Game(pid)
            game.update(gameinfo) # Actualizamos con la información de la partida global
            display = Display(game) # La pantalla para recibir los eventos
            while game.is_running():
                events = display.analyze_events()
                for ev in events:
                    conn.send(ev)
                    if ev == "quit":
                        game.stop()
                conn.send("next")
                gameinfo = conn.recv() # La información de la partida tras agregar el último guess
                game.update(gameinfo) # Actualizamos con la información de la partida global
                display.refresh()
                display.tick()
            print("------------------")
            if game.winner != "": # Si ha ganado un jugador
                if game.winner == game.pid: # Tu has ganado
                    print(f"you (player {pid}) won the game!")
                else: # Ha ganado otro jugador
                    print(f"you lost the game... player {game.winner} won")
            else: # No ha ganado nadie
                print(f"you lost the game... you ran out of tries")
            print(f"the secret word was {game.secret}")
            time.sleep(6) # tiempo que pasa desde que se acaba la partida hasta que se cierra la partida
    except:
        traceback.print_exc()
    finally:
        pygame.quit()

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
