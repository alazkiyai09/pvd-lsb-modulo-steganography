import numpy as np
import cv2
from PIL import Image
import binascii
import time
from CTR_DRBG import *

def lsb_embedding(Pi, M, K, Px, Px_next):
    """Embed 3 bits of message into the LSBs of pixel Pi's RGB channels using key-dependent masking."""
    M = binary_array(M)[5:]
    lpx, lpx_next = constant_pixel(Px, K), constant_pixel(Px_next, K)
    PR = binary_array(lpx^K)
    PG = binary_array(lpx_next^K)
    PB = binary_array((lpx^lpx_next)^K)

    AR = PR[(lpx*K)%8]
    AG = PG[(lpx_next*K)%8]
    AB = PB[(lpx*lpx_next*K)%8]
    Pi[0] = Pi[0] - (Pi[0]%2) + ((M[0])^AR)
    Pi[1] = Pi[1] - (Pi[1]%2) + ((M[1])^AG)
    Pi[2] = Pi[2] - (Pi[2]%2) + ((M[2])^AB)
    return Pi

def lsb_extraction(Pi, K, Px, Px_next):
    """Extract 3-bit message from pixel Pi's LSBs using key-dependent masking."""
    lpx, lpx_next = constant_pixel(Px, K), constant_pixel(Px_next, K)
    PR = binary_array(lpx^K)
    PG = binary_array(lpx_next^K)
    PB = binary_array((lpx^lpx_next)^K)

    AR = PR[(lpx*K)%8]
    AG = PG[(lpx_next*K)%8]
    AB = PB[(lpx*lpx_next*K)%8]

    MR = (Pi[0]%2)^AR
    MG = (Pi[1]%2)^AG
    MB = (Pi[2]%2)^AB

    M = 4*MR + 2*MG + 1*MB

    return M


def pvd_embedding(Pi, Px, M, K, out_of_bound, index, channel):
    """Embed message bit M into pixel using Pixel Value Differencing with key-dependent XOR."""
    pixel_i = Pi[channel]
    pixel_x = Px[channel]
    PA = constant_pixel(Px, K)^K
    d = abs(int(pixel_x) - int(pixel_i))
    dl = quantize_floor(d)
    du = dl + 3

    if dl == 0:
        R = d
    else:
        R = d%dl

    M = M^(PA%2)
    if R//2 != 0:
        d_new = dl + 2*(R%2) + M
    else:
        d_new = du - (2*(R%2) + M)

    if pixel_x >= pixel_i:
        Pi_new = pixel_x - d_new
    else:
        Pi_new = pixel_x + d_new

    if (Pi_new < 0 or Pi_new > 255):
        Pi_new = embedd_out_of_bound(Pi_new)
        out_of_bound.append(index)
        Pi[channel] = Pi_new
    else:
        Pi[channel] = Pi_new

    return R//2, Pi


def pvd_extraction(Pi, Px, K, metadata, out_of_bound, index, channel):
    """Extract message bit from pixel using PVD with key-dependent XOR."""
    if index in out_of_bound:
        pixel_i = extract_out_of_bound_pixel(Pi[channel])
    else:
        pixel_i = Pi[channel]

    pixel_x = Px[channel]
    d = abs(int(pixel_x)-int(pixel_i))
    dl = quantize_floor(d)
    du = dl + 3

    PA = constant_pixel(Px, K)^K
    if metadata !=0:
        X = d - dl
        M = (X%2)^(PA%2)
        R = abs(X-(X%2))//2 + 2*metadata
    else:
        X = du - d
        M = (X%2)^(PA%2)
        R = abs(X-(X%2))//2 + 2*metadata

    if pixel_x > pixel_i:
        Pi_old = pixel_x - (dl + R)
    else:
        Pi_old = pixel_x + (dl + R)

    Pi[channel] = Pi_old

    return M, Pi

def modulo_encoding(M):
    """Encode hex message into remainder (mod 8) and quotient (div 8) arrays."""
    Message = np.array([[0]*2]*len(M))
    for i in range(0, len(M)):
        Message[i][0] = int(M[i], 16)%8
        Message[i][1] = int(M[i], 16)//8

    Rem = Message[:][:,0]
    Div = Message[:][:,1]
    Rem = np.append(Rem, [0]*(3 - len(Div)%3))
    return Rem, Div

def constant_pixel(X, K):
    Y = (X[0] >> 2) + (X[1] >> 2) + (X[2] >> 2)
    return right_rotate((Y << 1), (K%8))

def quantize_floor(X):
    return (X//4)*4

def embedd_out_of_bound(P):
    if P < 0:
        P = abs(P)
    else:
        P = (255 - P)%256
    return P

def extract_out_of_bound_pixel(P):
    if P < 5:
        P = 0 - P
    elif P > 5:
        P = (256 - P) + 255
    return P

def optimizing(filename):
    cover = cv2.imread(filename)
    cover_rgb = cv2.cvtColor(cover, cv2.COLOR_BGR2RGB)
    wide, high = Image.open(filename).size

    cover_rgb = cover_rgb.reshape(wide*high, 3)
    channel = { '0':0, '1':0, '2':0}
    for i in range(0, len(cover_rgb)):
        channel['0'] = count_upper_and_lower(cover_rgb[i][0], channel['0'])
        channel['1'] = count_upper_and_lower(cover_rgb[i][1], channel['1'])
        channel['2'] = count_upper_and_lower(cover_rgb[i][2], channel['2'])

    channel = min(channel.keys(), key=(lambda k: channel[k]))
    return int(channel)


def count_upper_and_lower(P, count):
    if P == 0 or P == 255:
        count = count + 1

    return count

def binary_array(n):
    y = [int(x) for x in format(n,'08b')]
    return y

def right_rotate(n, d):
    INT_BITS = 32
    # In n>>d, first d bits are 0.
    # To put last 3 bits of at
    # first, do bitwise or of n>>d
    # with n <<(INT_BITS - d)
    x = (n >> d)|(n << (INT_BITS - d)) & 4294967295
    return x%(2**16)

def modulo_decoding(Rem, Div):
    """Decode remainder and quotient arrays back into hex message."""
    M = np.array([[0]*2]*len(Div))
    M[:][:,0] = Rem
    M[:][:,1] = Div
    Message = np.array(['']*len(M))
    for i in range(0, len(M)):
        Message[i] = hex(M[i][0] + M[i][1]*8)[2:]

    return Message

def read_file(filename):
    """Read a binary file and return its content as a hex string."""
    try:
        with open(filename, 'rb') as f:
            hexdata = f.read().hex()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {filename}")
    except IOError as e:
        raise IOError(f"Error reading file {filename}: {e}")
    return hexdata

def write_file(filename, hexdata):
    """Write hex string data to a binary file."""
    try:
        hexdata = binascii.unhexlify(hexdata)
        with open(filename, "wb") as f:
            f.write(hexdata)
    except IOError as e:
        raise IOError(f"Error writing file {filename}: {e}")

def save_metadata(metadata, param1, param2, param3, param4, number_of_block, out_of_bound, channel):
    temp = ''
    metadata1 = metadata_to_byte(metadata)
    #print(len(metadata1))
    for i in range(0, len(param4)):
        temp = temp + str(param4[i]) + 'aaaa'
    if len(temp) == 0:
        temp = 'ee'
    metadata2 = str(param1) + 'cccc' + str(param2) + 'cccc' + str(param3) + 'cccc' + str(temp)
    temp = ''
    for i in range(0, len(out_of_bound)):
        temp = temp + str(out_of_bound[i]) + 'bbbb'
    if len(temp) == 0:
        temp = 'ee'
    metadata3 = str(number_of_block)
    full_metadata = metadata3 + 'ffff' + metadata2 + 'ffff' + str(temp) + metadata1 + str(channel)
    full_metadata = '0'*(2 - len(full_metadata)%2) + full_metadata
    text_file = open("metadata.txt", "w")
    n = text_file.write(full_metadata)
    text_file.close()
    write_file('Metadata2.txt', full_metadata)

def metadata_to_byte(metadata):
    i = 0
    meta = ''
    m = np.append(metadata, [0]*(4 - len(metadata)%4))
    while i < len(m):
        temp = ''.join(str(e) for e in m[i:i+4])
        meta = meta + hex(int(temp, 2))[2:]
        i = i + 4

    return meta

def metadata_to_array(hexdata):
    metadata = np.array([])
    for i in range(0, len(hexdata)):
        metadata = np.append(metadata, binary_array(int(hexdata[i], 16))[4:])
    return metadata

def extract_metadata(filename):
    full_metadata = str(read_file(filename))
    i = 0
    stop = False
    number_of_message = 0
    channel = int(full_metadata[len(full_metadata)-1])
    full_metadata = full_metadata[:len(full_metadata)-1]
    while stop == False:
        if full_metadata[i:i+4] == 'ffff' and full_metadata[i+4] != 'f' and number_of_message == 0:
            number_of_message = int(full_metadata[:i])
            metadata = full_metadata[i+4:len(full_metadata)-(number_of_message*3//16)-1]
            pvd_parameter = full_metadata[len(full_metadata)-(number_of_message*3//16)-1:]
            stop = True
        i = i + 1

    stop = False
    upper = 0
    while stop == False:
        if metadata[i:i+4] == 'ffff' and metadata[i+4] != 'f':
            metadata2 = metadata[:i]
            metadata = metadata[i+4:]
            stop = True
        i = i + 1

    out_of_bound = extract_out_of_bound(metadata)
    param1, param2, param3, param4 = extract_param_random(metadata2)

    return param1, param2, param3, param4, out_of_bound, number_of_message, pvd_parameter, channel


def extract_out_of_bound(metadata):
    stop = False
    out_of_bound = []
    i = 0
    if metadata == 'ee':
        out_of_bound = []
        stop = True
    else:
        metadata = metadata + ' '
    while stop == False and metadata[i] !='':
        if metadata[i:i+4] == 'bbbb' and metadata[i+4] != 'b':
            out_of_bound.append(int(metadata[:i]))
            if metadata[i+4:] != ' ':
                metadata = metadata[i+4:]
                i = 0
            else:
                stop = True

        i = i + 1

    return out_of_bound

def extract_param_random(metadata):
    stop = False
    param = []
    i = 0
    while stop == False:
        if metadata[i:i+4] == 'cccc' and metadata[i+4] != 'c':
            param.append(metadata[:i])
            if metadata[i+4:] != '':
                metadata = metadata[i+4:]
                i = 0
            else:
                stop = True
            if len(param) == 3:
                stop = True

        i = i + 1

    stop = False
    param4 = []
    i = 0

    while stop == False:
        if metadata == 'ee':
            param4 = []
            stop = True
        if metadata[i:i+4] == 'aaaa' and metadata[i+4] != 'a':
            param4.append(metadata[:i])
            if metadata[i+4:] != '':
                metadata = metadata[i+4:]
            else:
                stop = True

        i = i + 1


    return str(param[0].upper()), str(param[1].upper()), str(param[2].upper()), param4

def embedding_process(filename, Rem, Div, V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_message, channel):
    """Embed message into cover image using PVD + LSB with modulo encoding."""
    cover = cv2.imread(filename)
    cover_rgb = cv2.cvtColor(cover, cv2.COLOR_BGR2RGB)

    wide, high = Image.open(filename).size
    total_pixels = wide * high
    required_pixels = len(Rem) + (len(Rem) // 3) * 2 + 10
    if required_pixels > total_pixels:
        raise ValueError(
            f"Message too large for image: needs ~{required_pixels} pixels, "
            f"but image has {total_pixels} pixels ({wide}x{high})"
        )
    metadata = np.array([0]*((number_of_message)*3//4))
    cover_rgb = cover_rgb.reshape(wide*high, 3)

    out_of_bound = []

    i = 0
    j = 0
    l = 0
    r = 0
    P1 = cover_rgb[j]
    Px = cover_rgb[j+1]
    P2 = cover_rgb[j+2]
    Px_next = cover_rgb[j+4]
    #print("Cover", cover_rgb[:10])
    Div1, Div2 = Div[:(len(Rem)//3)*2], Div[(len(Rem)//3)*2:]

    while (j < len(Rem)) and (j<len(cover_rgb)) :
        if r%16 == 0:
            returned_bits, Key, V, reseed_counter, entropy_inputs = CTR_DRBG_Generate(V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs)
            returned_bits = split_random(returned_bits)
            K = returned_bits[0]%(2**16)
            r = r + 1
        else:
            K = returned_bits[r%16]%(2**16)
            r = r + 1

        cover_rgb[j] = lsb_embedding(P1, Rem[j], K, Px, Px_next)
        cover_rgb[j+1] = lsb_embedding(Px, Rem[j+1], K, Px, Px_next)
        cover_rgb[j+2] = lsb_embedding(P2, Rem[j+2], K, Px, Px_next)

        P1 = cover_rgb[j]
        Px = cover_rgb[j+1]
        P2 = cover_rgb[j+2]
        #print("After LSB", cover_rgb[:10])
        metadata[i], cover_rgb[j] = pvd_embedding(P1, Px, Div1[i], K, out_of_bound, j, channel)
        metadata[i+1], cover_rgb[j+2] = pvd_embedding(P2, Px, Div1[i+1], K, out_of_bound, j+2, channel)

        i = i + 2
        j = j + 3
        l = l + 1

        P1 = cover_rgb[j]
        Px = cover_rgb[j+1]
        P2 = cover_rgb[j+2]
        Px_next = cover_rgb[j+4]

    Div2 = np.append(Div2, [0]*(11 - len(Div2)%11))
    l = 0
    while l < len(Div2):
        if r%16 == 0:
            returned_bits, Key, V, reseed_counter, entropy_inputs = CTR_DRBG_Generate(V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs)
            returned_bits = split_random(returned_bits)
            K = returned_bits[0]%(2**16)
            r = r + 1
        else:
            K = returned_bits[r%16]%(2**16)
            r = r + 1

        Temp = [(Div2[l]*4+Div2[l+1]*2+Div2[l+2]*1), (Div2[l+3]*4+Div2[l+4]*2+Div2[l+5]*1), (Div2[l+6]*4+Div2[l+7]*2+Div2[l+8]*1)]

        cover_rgb[j] = lsb_embedding(P1, Temp[0], K, Px, Px_next)
        cover_rgb[j+1] = lsb_embedding(Px, Temp[1], K, Px, Px_next)
        cover_rgb[j+2] = lsb_embedding(P2, Temp[2], K, Px, Px_next)

        P1 = cover_rgb[j]
        Px = cover_rgb[j+1]
        P2 = cover_rgb[j+2]

        l = l + 9

        metadata[i], cover_rgb[j] = pvd_embedding(P1, Px, Div2[l], K, out_of_bound, j, channel)
        metadata[i+1], cover_rgb[j+2] = pvd_embedding(P2, Px, Div2[l+1], K, out_of_bound, j+2, channel)

        l = l + 2
        j = j + 3
        i = i + 2

        P1 = cover_rgb[j]
        Px = cover_rgb[j+1]
        P2 = cover_rgb[j+2]
        Px_next = cover_rgb[j+4]
    #print("Stego", cover_rgb[:10])
    #print("Number of Random Number", r)
    stego = cover_rgb.reshape(high, wide, 3)
    stego = cv2.cvtColor(stego, cv2.COLOR_RGB2BGR)
    return stego, metadata, entropy_inputs, out_of_bound

def extraction_process(filename1, hexdata, V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_message, out_of_bound, channel):
    """Extract hidden message from stego image using PVD + LSB with modulo decoding."""
    stego = cv2.imread(filename1)
    stego_rgb = cv2.cvtColor(stego, cv2.COLOR_BGR2RGB)

    wide, high = Image.open(filename1).size
    stego_rgb = stego_rgb.reshape(wide*high, 3)

    Rem = np.array([0]*number_of_message)
    Div = np.array([0]*number_of_message)
    Rem = np.append(Rem, [0]*(3 - (number_of_message)%3))
    Div1, Div2 = Div[:(len(Rem)//3)*2], Div[(len(Rem)//3)*2:]
    metadata = metadata_to_array(hexdata)

    i = 0
    j = 0
    l = 0
    r = 0

    P1 = stego_rgb[j]
    Px = stego_rgb[j+1]
    P2 = stego_rgb[j+2]
    Px_next = stego_rgb[j+4]
    number_of_reseed = 0
    while (j < len(Rem)) and (j<len(stego_rgb)) :
        if r%16 == 0:
            returned_bits, Key, V, reseed_counter, number_of_reseed = CTR_DRBG_Regenerate(V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_reseed)
            returned_bits = split_random(returned_bits)
            K = returned_bits[0]%(2**16)
            r = r + 1
        else:
            K = returned_bits[r%16]%(2**16)
            r = r + 1

        Div1[i], stego_rgb[j] = pvd_extraction(P1, Px, K, metadata[i], out_of_bound, j, channel)
        Div1[i+1], stego_rgb[j+2] = pvd_extraction(P2, Px, K, metadata[i+1], out_of_bound, j+2, channel)

        P1 = stego_rgb[j]
        P2 = stego_rgb[j+2]

        Rem[j] = lsb_extraction(P1, K, Px, Px_next)
        Rem[j+1] = lsb_extraction(Px, K, Px, Px_next)
        Rem[j+2] = lsb_extraction(P2, K, Px, Px_next)

        j = j + 3
        i = i + 2
        l = l + 1

        P1 = stego_rgb[j]
        Px = stego_rgb[j+1]
        P2 = stego_rgb[j+2]
        Px_next = stego_rgb[j+4]

    Div2 = np.append(Div2, [0]*(11 - len(Div2)%11))
    l = 0
    while l < len(Div2):
        if r%16 == 0:
            returned_bits, Key, V, reseed_counter, number_of_reseed = CTR_DRBG_Regenerate(V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_reseed)
            returned_bits = split_random(returned_bits)
            K = returned_bits[0]%(2**16)
            r = r + 1
        else:
            K = returned_bits[r%16]%(2**16)
            r = r + 1

        Div2[l+9], stego_rgb[j] = pvd_extraction(P1, Px, K, metadata[i], out_of_bound, j, channel)
        Div2[l+10], stego_rgb[j+2] = pvd_extraction(P2, Px, K, metadata[i+1], out_of_bound, j+2, channel)

        P1 = stego_rgb[j]
        P2 = stego_rgb[j+2]

        Temp = lsb_extraction(P1, K, Px, Px_next)
        Temp = binary_array(Temp)[5:]

        Div2[l] = Temp[0]
        Div2[l+1] = Temp[1]
        Div2[l+2] = Temp[2]

        Temp = lsb_extraction(Px, K, Px, Px_next)
        Temp = binary_array(Temp)[5:]
        Div2[l+3] = Temp[0]
        Div2[l+4] = Temp[1]
        Div2[l+5] = Temp[2]

        Temp = lsb_extraction(P2, K, Px, Px_next)
        Temp = binary_array(Temp)[5:]
        Div2[l+6] = Temp[0]
        Div2[l+7] = Temp[1]
        Div2[l+8] = Temp[2]

        j = j + 3
        i = i + 2
        l = l + 11

        P1 = stego_rgb[j]
        Px = stego_rgb[j+1]
        P2 = stego_rgb[j+2]
        Px_next = stego_rgb[j+4]


    stego_rgb  = stego_rgb.reshape(high, wide, 3)
    Rem = Rem[:number_of_message]
    Div = np.append(Div1, Div2)
    Div = Div[:number_of_message]
    print(Rem, Div)
    Message = modulo_decoding(Rem, Div)
    Message = ''.join(str(e) for e in Message[:])

    return Message


def embedding():
    start = time.time()
    filename1 = "Image 65.png"
    filename2 = "Input.txt"

    entropy_input = '808182838485868788898A8B8C8D8E8F909192939495969798999A9B9C'
    nonce = '20212223242526'
    personalization_string = '404142434445464748494A4B4C4D4E4F505152535455565758595A5B5C'
    additional_input = ''
    security_strength = 128
    requested_number_of_bit = 512
    entropy_inputs = []
    out_of_bound = []
    V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, security_strength)

    M = read_file(filename2)
    Rem, Div = modulo_encoding(M)
    number_of_message = len(Div)

    channel = optimizing(filename1)

    stego, metadata, entropy_inputs, out_of_bound = embedding_process(filename1, Rem, Div, V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_message, channel)

    cv2.imwrite("stego.tiff", stego)

    save_metadata(metadata, entropy_input, nonce, personalization_string, entropy_inputs, number_of_message, out_of_bound, channel)
    total_time = time.time() - start
    print(Rem, Div)
    print("Time Execution: ", total_time)
    print("Out of Bound", (out_of_bound), len(out_of_bound))
    print("ENTROPY INPUT: ", entropy_inputs, len(entropy_inputs))

def extraction():
    start = time.time()
    filename1 = 'stego.tiff'
    filename2 = 'Metadata2.txt'
    entropy_input, nonce, personalization_string, entropy_inputs, out_of_bound, number_of_message, pvd_parameter, channel = extract_metadata(filename2)
    additional_input = ''
    security_strength = 128
    requested_number_of_bit = 512
    print("Param 1", entropy_input)
    print("Param 2", nonce)
    print("Param 3", personalization_string)
    print("Param 4", entropy_inputs)
    print("out_of_bound", out_of_bound, len(out_of_bound))
    V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, security_strength)
    Message = extraction_process(filename1, pvd_parameter, V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_message, out_of_bound, channel)
    write_file("Output.txt", Message)
    total_time = time.time() - start
    print("Time Execution: ", total_time)


if __name__ == '__main__':
    embedding()
    extraction()
