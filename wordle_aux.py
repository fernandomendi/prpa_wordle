from random import choice
import pygame

# Elegir la escala en función de la resolución de vuestra pantalla
scale = 1
# scale = 0.66

# CONSTANTES GLOBALES
# -----------------------------------------------------------------------------------

WORD_LENGTH = 5
N_TRIES = 6

SQUARE_WIDTH = int(80*scale)
SQUARE_BORDER = int(2*scale)
SQUARE_XPAD = int(10*scale)
SQUARE_YPAD = int(20*scale)

X_OFFSET = int(30*scale)
Y_OFFSET = int(50*scale)

GRID_HEIGHT = N_TRIES*SQUARE_WIDTH + (N_TRIES-1)*SQUARE_YPAD
GRID_WIDTH = WORD_LENGTH*SQUARE_WIDTH + (WORD_LENGTH-1)*SQUARE_XPAD

WIDTH = 2*X_OFFSET + GRID_WIDTH
HEIGHT = 2*Y_OFFSET + 3*SQUARE_YPAD + GRID_HEIGHT + 2*SQUARE_WIDTH + SQUARE_BORDER

GREEN = "#6AAA64"
YELLOW = "#C9B458"
GREY = "#787C7E"
LIGHT_GREY = "#E1E1E1"
WHITE = "#FFFFFF"
BLACK = "#000000"
RED = "#E11D48"

def getWords(): # Obtenemos la lista de todas las palabras
    words = []
    with open("words.txt", "r") as f:
        for word in f:
            words.append(word.strip())
    return words

def getSecretWord(words): # Elige una palabra aleatoria de la lista
    return choice(words).strip()

class Square: # Las casillas que vemos en la pantalla
    def __init__(self, letter=None, color=None, guess=False):
        pygame.init()
        self.letter = letter
        self.color = color
        self.guess = guess

    def draw(self): # Dibuja una casilla
        square = pygame.Surface((SQUARE_WIDTH, SQUARE_WIDTH))
        innerSquare = pygame.Surface((SQUARE_WIDTH - 2 * SQUARE_BORDER, SQUARE_WIDTH - 2 * SQUARE_BORDER))
        if self.guess: # Para distinguir entre las casillas de la cuadricula general y las de la fila de guess local
            innerSquare.fill(LIGHT_GREY)
        else: # Las de la cuadricula general serán blancas
            innerSquare.fill(WHITE)
        if self.letter == None: # Si no hay letra, entonces la casilla tendrá borde
            square.blit(innerSquare, (SQUARE_BORDER, SQUARE_BORDER))
        else:
            if self.color == None: # Si hay letra pero no está coloreada, entonces la casilla tendrá borde
                square.blit(innerSquare, (SQUARE_BORDER, SQUARE_BORDER))
                letter = pygame.font.Font(None, SQUARE_WIDTH).render(self.letter.upper(), True, BLACK)
            else:
                if self.color == "0":
                    square.fill(GREEN)
                elif self.color == "1":
                    square.fill(YELLOW)
                elif self.color == "2":
                    square.fill(GREY)
                letter = pygame.font.Font(None, SQUARE_WIDTH).render(self.letter.upper(), True, WHITE)
            letter_rect = letter.get_rect(center=(SQUARE_WIDTH//2, SQUARE_WIDTH//2)) # Centrar la letra en el cuadrado
            square.blit(letter, letter_rect)
        return square

def draw_grid(screen, matrix): # Dibuja la cuadricula completa
    for i in range(N_TRIES):
        for j in range(WORD_LENGTH):
            square = matrix[i][j]
            screen.blit(square.draw(), (X_OFFSET + j*(SQUARE_WIDTH + SQUARE_XPAD), Y_OFFSET + i*(SQUARE_WIDTH + SQUARE_YPAD)))

def draw_divider(screen): # Dibuja la linea entre la cuadricula y la fila del guess local
    divider = pygame.Surface((WIDTH - X_OFFSET, SQUARE_BORDER))
    screen.blit(divider, (X_OFFSET // 2, Y_OFFSET + GRID_HEIGHT + SQUARE_YPAD))

def draw_guess_row(screen, guess_row): # Dibuja la fila del guess local
    for j, sq in enumerate(guess_row):
        screen.blit(sq.draw(), (X_OFFSET + j*(SQUARE_WIDTH + SQUARE_XPAD), Y_OFFSET + GRID_HEIGHT + 2*SQUARE_YPAD + SQUARE_BORDER))

def render_message(screen, message): # Dibuja el mensaje (si hay) al final de la pantalla
    msg = pygame.font.Font(None, SQUARE_WIDTH // 2).render(message, True, RED)
    msg_rect = msg.get_rect()
    msg_rect.center = ((GRID_WIDTH) // 2, (SQUARE_WIDTH) // 2)
    bounds = pygame.Surface((GRID_WIDTH, SQUARE_WIDTH))
    bounds.fill(WHITE)
    bounds.blit(msg, msg_rect)
    screen.blit(bounds, (X_OFFSET, Y_OFFSET + GRID_HEIGHT + 3*SQUARE_YPAD + SQUARE_BORDER + SQUARE_WIDTH))

def get_word_from_row(row, j): # Obtenemos la palabra en formato "String" a partir de la fila del guess local
    word = ""
    for k in range(j):
        word += row[k].letter
    return word

def resetRow(guess_row): # Vaciamos la fila del guess local
    for sq in guess_row:
        sq.letter = None
    return guess_row
    
def replaceLetterAtIndex(word, letter, i):
    return word[:i] + letter + word[i+1:]

def getColorsFromGuess(guess, secret): # Evaluamos la palabra y devolvemos los correspondientes colores de cada letra
    """
    0 - VERDE
    1 - AMARILLO
    2 - GRIS
    """
    answer = "2" * WORD_LENGTH
    counted = {}
    for i, letter in enumerate(guess):
        if letter not in counted:
            counted[letter] = 0
        if letter == secret[i]:
            answer = replaceLetterAtIndex(answer, "0", i)
            counted[letter] += 1
    for i, letter in enumerate(guess):
        if letter in secret:
            cntWord = secret.count(letter)
            if cntWord > counted[letter] and answer[i] == "2":
                answer = replaceLetterAtIndex(answer, "1", i)
                counted[letter] += 1
    return answer
