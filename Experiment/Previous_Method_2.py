import numpy as np
import pandas as pd
from numpy import *
import cv2
from PIL import Image
from matplotlib import pyplot as plt
import matplotlib
import binascii
import time


def msldip_embedding(Pi, M):
    """Embed single digit M into pixel Pi using MSLDIP (modify last digit in base-10)."""
    Pi = Pi - Pi%10 + M
    return Pi

def msldip_extraction(Pi):
    """Extract embedded digit from pixel Pi (last digit in base-10)."""
    M = Pi%10
    return M

def read_file(filename):
    with open(filename, 'r') as f:
        data = f.read()
    #print(data)
    return data

def mpk_encoding(M):
    """Encode text message M using MPK character-to-digit mapping."""
    mpk = []
    dictionary = {' ':0, '!':1, '"':3,'#':4, '$':5, '%':6, '&':7, '\'':8, '(':9, ')':10,
    '*':11, '+':12, ',':13, '-':14, '.':15, '/':16, '0':2, '1':17, '2':24, '3':34, '4':44,
    '5':54, '6':64, '7':75, '8':84, '9':95, ':':18, ';':19, '<':20, '=':28, '>':29, '?':30,
    '@':38, 'A':25, 'B':26, 'C':27, 'D':35, 'E':36, 'F':37, 'G':45, 'H':46, 'I':47, 'J':55,
    'K':56, 'L':57, 'M':65, 'N':66, 'O':67, 'P':76, 'Q':77, 'R':78, 'S':79, 'T':85, 'U':86,
    'V':87, 'W':96, 'X':97, 'Y':98, 'Z':99, '[':39, '\\':40, '^':48 , '_':50, 'a':21, 'b':22,
    'c':23, 'd':31, 'e':32, 'f':33, 'g':41, 'h':42, 'i':43, 'j':51, 'k':52, 'l':53, 'm':61,
    'n':62, 'o':63, 'p':71, 'q':72, 'r':73, 's':74, 't':81, 'u':82, 'v':83, 'w':91, 'x':92,
    'y':93, 'z':94, '{':59, '|':60, '}':68}

    for i in range(0, len(M)):
        temp = dictionary[M[i]]
        mpk.append(temp//10)
        mpk.append(temp%10)

    return np.array(mpk)

def range_table(d):
    li = (d//5)*5
    ui = li + 4

    return li, ui


def pvd_embedding(Pi, Px, d, M):
    """Embed digit M into pixel pair (Pi, Px) using PVD when difference d < 20."""
    li, ui = range_table(d)
    d_new = li + M/2
    Rem = M%2

    if Pi >= Px and d_new > d:
        Pi = Pi + int(np.ceil(M/2))
        Px = Px - M//2
    elif Pi < Px and d_new > d:
        Pi = Pi - M//2
        Px = Px + int(np.ceil(M/2))
    elif Pi >= Px and d_new <= d:
        Pi = Pi - int(np.ceil(M/2))
        Px = Px + M//2
    elif Pi < Px and d_new <= d:
        Pi = Pi + int(np.ceil(M/2))
        Px = Px - M//2

    return Pi, Px
def embedding_process(filename1, filename2):
    """Embed message from filename2 into cover image filename1 using MSLDIP + PVD."""
    M = read_file(filename2)
    M = mpk_encoding(M)

    cover = cv2.imread(filename1)
    cover_rgb = cv2.cvtColor(cover, cv2.COLOR_BGR2RGB)
    wide, high = Image.open(filename1).size
    cover_rgb = cover_rgb.reshape(wide*high*3, 1)
    j = 0
    i = 0
    while (i < len(M)):
        Pi = cover_rgb[j]
        Px = cover_rgb[j+1]

        d = abs(Pi - Px)

        if d < 20:
            Pi, Px = pvd_embedding(Pi, Px, d, M[i])
            cover_rgb[j] = Pi
            cover_rgb[j+1] = Px
            i = i + 1
        else:
            Pi = msldip_embedding(Pi, M[i])
            cover_rgb[j] = Pi
            i = i + 1
            Px = msldip_embedding(Px, M[i])
            cover_rgb[j+1] = Px
            i = i + 1
        j = j + 2

    stego = cover_rgb.reshape(high, wide, 3)
    stego = cv2.cvtColor(stego, cv2.COLOR_RGB2BGR)
    return stego
