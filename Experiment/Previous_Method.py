import numpy as np
import pandas as pd
from numpy import *
import cv2
from PIL import Image
from matplotlib import pyplot as plt
import matplotlib
import binascii
import time


def lsb_embedding(Px, M):
    """Embed message bits M into the LSBs of pixel value Px with overflow correction."""
    P = binary_array(Px)
    L = int(''.join(str(e) for e in P[-len(M):]), 2)
    P = np.append(P[:5], M)
    temp = ''.join(str(e) for e in P)
    Px_new = int(temp, 2)
    S = int(''.join(str(e) for e in P[-len(M):]), 2)
    #print(S, L)
    d = L - S
    if (d > 2**(len(M)-1)) and ((Px_new + 2**(len(M))) >= 0) and ((Px_new + 2**(len(M))) <= 255):
        Px =  Px_new + 2**(len(M))
    elif (d < -2**(len(M)-1)) and ((Px_new - 2**(len(M))) >= 0) and ((Px_new - 2**(len(M))) <= 255):
        Px =  Px_new - 2**(len(M))
    else:
        Px = Px_new
        #print(Px)
    return Px

def lsb_extraction(Px):
    """Extract the last 3 bits (LSBs) from pixel value Px."""
    P = binary_array(Px)
    M = P[-3:]
    return M

def pvd_embedding(Pi, Px, M, li):
    """Embed message bits M into pixel Pi using PVD with reference pixel Px."""
    si = int(''.join(str(e) for e in M), 2)
    d = li + si
    Pi2  = Px - d
    Pi3 = Px + d
    if Pi2 < 0:
        Pi = Pi3
    elif Pi3 > 255:
        Pi = Pi2
    elif (abs(Pi - Pi2) < abs(Pi-Pi3)) and (Pi2>=0) and (Pi3 <=255):
        Pi = Pi2
    else:
        Pi = Pi3
    #print(Pi)
    return Pi

def pvd_extraction(Pi, Px):
    """Extract message bits from pixel pair (Pi, Px) using PVD."""
    d = abs(Pi - Px)
    cap, li = range_d(d)
    s = d - li
    M = binary_array(s)[-cap:]
    return M, cap

def range_d(d):
    """Return (embedding capacity, lower bound) for a given pixel difference d per PVD range table."""
    if d >= 0 and d <=7:
        M = 3
        li = 0
    elif d >= 8 and d<=15:
        M = 3
        li = 8
    elif d>=16 and d<=31:
        M = 3
        li = 16
    elif d>=32 and d<=63:
        M = 4
        li = 32
    else:
        # d >= 64 (covers d > 255 which could occur with out-of-bound pixels)
        M = 4
        li = 64

    return M, li

def binary_array(n):
    y = np.array([int(x) for x in format(n,'08b')])
    return y

def read_file(filename):
    with open(filename, 'rb') as f:
        hexdata = f.read().hex()
    return hexdata

def write_file(filename, hexdata):
    hexdata = binascii.unhexlify(hexdata)
    with open(filename, "wb") as f: f.write(hexdata)

def convert_message(filename):
    M = read_file(filename)
    Message = np.array([[0]*4]*len(M))

    for i in range(0, len(M)):
        Message[i][:] = np.array([int(x) for x in format(int(M[i], 16),'04b')])
    Message = Message.ravel()
    return Message

def bin_to_hex(M):
    i = 0
    hexa = ''
    while i < len(M):
        #print(M[i:i+4])
        temp = hex(int(''.join(str(e) for e in M[i:i+4]), 2))[2:]
        hexa = hexa + temp
        i = i + 4
    return hexa


def embedding_process(filename, M):
    """Embed binary message M into cover image using LSB + PVD."""
    cover = cv2.imread(filename)
    cover_rgb = cv2.cvtColor(cover, cv2.COLOR_BGR2RGB)

    wide, high = Image.open(filename).size

    cover_rgb = cover_rgb.reshape(wide*high, 3)

    j = 0
    i = 0
    while i < len(M):

        cover_rgb[j][0] = lsb_embedding(cover_rgb[j][0], M[i:i+3])
        i = i + 3
        for k in range(0, 2):
            d = abs(int(cover_rgb[j][0]) - int(cover_rgb[j][k+1]))
            Msg, li = range_d(d)
            if i+Msg > len(M):
                break
            cover_rgb[j][k+1] = pvd_embedding(int(cover_rgb[j][k+1]), int(cover_rgb[j][0]), M[i:i+Msg], li)
            i = i + Msg
        j = j + 1
        for k in range(0, 3):
            d = abs(int(cover_rgb[j-1][0]) - int(cover_rgb[j][k]))
            Msg, li = range_d(d)
            if i+Msg > len(M):
                break
            cover_rgb[j][k] = pvd_embedding(int(cover_rgb[j][k]), int(cover_rgb[j-1][0]), M[i:i+Msg], li)
            i = i + Msg
        j = j + 1

    stego = cover_rgb.reshape(high, wide, 3)
    stego = cv2.cvtColor(stego, cv2.COLOR_RGB2BGR)
    return stego

def extraction_process(filename1, size_message):
    """Extract binary message of given size from stego image using LSB + PVD."""
    stego = cv2.imread(filename1)
    stego_rgb = cv2.cvtColor(stego, cv2.COLOR_BGR2RGB)

    wide, high = Image.open(filename1).size
    stego_rgb = stego_rgb.reshape(wide*high, 3)
    message = np.array([0]*size_message)

    j = 0
    i = 0
    while i < len(message) - 2:
        message[i:i+3] = lsb_extraction(stego_rgb[j][0])
        i = i + 3
        for k in range(0, 2):
            temp, cap = pvd_extraction(int(stego_rgb[j][k+1]), int(stego_rgb[j][0]))
            if i+cap > len(message):
                break
            message[i:i+cap] = temp
            i = i + cap
        j = j + 1
        for k in range(0, 3):
            temp, cap = pvd_extraction(int(stego_rgb[j][k]), int(stego_rgb[j-1][0]))
            if i+cap > len(message):
                break
            message[i:i+cap] = temp
            i = i + cap
        j = j + 1

    return message

