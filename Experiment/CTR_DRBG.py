"""CTR_DRBG: Deterministic Random Bit Generator based on NIST SP 800-90A.

Implements AES-128-CTR_DRBG for generating pseudorandom sequences used
in the steganographic embedding/extraction process.

NOTE (NIST Spec Deviation): The rightmost() function uses V[:-a] which
returns the leftmost bits instead of the rightmost bits per NIST SP 800-90A.
This means in CTR_DRBG_Update(), Key and V both derive from the first portion
of temp rather than Key=first 128 bits, V=last 128 bits as specified.
Since both Generate and Regenerate use the same implementation, the
embedding/extraction round-trip remains consistent. DO NOT FIX this without
re-validating all existing stego images, as it would break compatibility.
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import numpy as np


def CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, security_strength):
    """Instantiate the CTR_DRBG with seed material derived from entropy, nonce, and personalization string."""
    keylen = 128
    blocklen = 128
    seedlen = 256
    seed_material = entropy_input + nonce + personalization_string
    seed_material = Block_Cipher_df(seed_material, seedlen)
    Key = '0'*keylen
    V = '0'*blocklen
    Key, V = CTR_DRBG_Update(seed_material, Key, V)
    reseed_counter = 1
    return V, Key, reseed_counter

def BCC(Key, data):
    """Block Cipher Chaining: CBC-MAC using AES as the block cipher."""
    outlen = 128
    chaining_value = '0'*outlen
    n = len(data)//outlen
    for i in range(0, n):
        block = data[(i)*outlen: (i+1)*outlen]
        input_block = xor(chaining_value, block)
        chaining_value = block_encrypt(Key, input_block)
    output_block = chaining_value
    return output_block

def Block_Cipher_df(input_string, number_of_bits_to_return):
    """Derivation function using AES block cipher (NIST SP 800-90A Section 10.3.2)."""
    keylen = 128
    outlen = 128
    max_number_of_bits = 2**48
    if(number_of_bits_to_return > max_number_of_bits):
        return ''
    L = len(input_string)
    N = number_of_bits_to_return//8
    S = str(L) + str(N) + input_string + '80'
    while ((len(S)*4)%outlen) != 0 :
        S = S + '0'
    temp = ''
    i = 0
    # NIST SP 800-90A Section 10.3.2: Fixed key for the derivation function
    K = '000102030405060708091A1B1C1D1E1F'
    while (len(temp)*4) < (keylen + outlen) :
        IV = format(i,'032b') + '0'*(outlen - (32))
        temp = temp + BCC(K, (IV + S))
        #print("TEMP", temp)
        i = i + 1
    K = leftmost(temp, keylen)

    X = select(temp, keylen+1, keylen+outlen)
    #print("XX", X)
    temp = ''
    while ((len(temp)*4) < number_of_bits_to_return):
        X = block_encrypt(K, X)
        temp = temp + str(X)
    requested_bits = leftmost(temp, number_of_bits_to_return)
    return requested_bits

def CTR_DRBG_Generate(V, Key, reseed_counter, requested_number_of_bits, additional_input, entropy_inputs):
    """Generate pseudorandom bits, automatically reseeding if the counter exceeds the interval."""
    reseed_interval = 10000
    seedlen = 256
    blocklen  = 128
    ctr_len = 64
    if reseed_counter > reseed_interval:
        entropy_inputs.append(new_entropy())
        entropy_input = entropy_inputs[len(entropy_inputs)-1]
        V, Key, reseed_counter = CTR_DRBG_Reseed(V, Key, reseed_counter, entropy_input, additional_input)
    if (additional_input != '' ):
        additional_input = Block_Cipher_df(additional_input, seedlen)
        Key, V = CTR_DRBG_Update(additional_input, Key, V)
    else:
        additional_input = '0'*seedlen
    temp = ''
    while ((len(temp)*4) < requested_number_of_bits):
        if (ctr_len < blocklen):
            inc = (int(rightmost(V, ctr_len), 16))% 2**(ctr_len)
            V = leftmost(V, blocklen - ctr_len) + bin_to_hex(format(inc, '0'+str(ctr_len)+'b'))
        else:
            V = int(V + 1) % 2**blocklen
        output_block = block_encrypt(Key, V)
        temp = temp + output_block
    returned_bits = leftmost(temp, requested_number_of_bits)
    Key, V = CTR_DRBG_Update(additional_input, Key, V)
    reseed_counter = reseed_counter + 1
    return returned_bits, Key, V, reseed_counter, entropy_inputs

def CTR_DRBG_Regenerate(V, Key, reseed_counter, requested_number_of_bits, additional_input, entropy_inputs, number_of_reseed):
    """Regenerate pseudorandom bits deterministically for extraction (uses stored entropy inputs)."""
    reseed_interval = 10000
    seedlen = 256
    blocklen  = 128
    ctr_len = 64
    if reseed_counter > reseed_interval:
        entropy_input = entropy_inputs[number_of_reseed]
        V, Key, reseed_counter = CTR_DRBG_Reseed(V, Key, reseed_counter, entropy_input, additional_input)
        number_of_reseed = number_of_reseed + 1
    if (additional_input != '' ):
        additional_input = Block_Cipher_df(additional_input, seedlen)
        Key, V = CTR_DRBG_Update(additional_input, Key, V)
    else:
        additional_input = '0'*seedlen
    temp = ''
    while ((len(temp)*4) < requested_number_of_bits):
        if (ctr_len < blocklen):
            inc = (int(rightmost(V, ctr_len), 16))% 2**(ctr_len)
            V = leftmost(V, blocklen - ctr_len) + bin_to_hex(format(inc, '0'+str(ctr_len)+'b'))
        else:
            V = int(V + 1) % 2**blocklen
        output_block = block_encrypt(Key, V)
        temp = temp + output_block
    returned_bits = leftmost(temp, requested_number_of_bits)
    Key, V = CTR_DRBG_Update(additional_input, Key, V)
    reseed_counter = reseed_counter + 1
    return returned_bits, Key, V, reseed_counter, number_of_reseed

def CTR_DRBG_Reseed(V, Key, reseed_counter, entropy_input, additional_input):
    """Reseed the DRBG state with fresh entropy."""
    seedlen = 256
    seed_material = entropy_input + additional_input
    seed_material = Block_Cipher_df(seed_material, seedlen)
    Key, V = CTR_DRBG_Update(seed_material, Key, V)
    reseed_counter = 1
    return V, Key, reseed_counter

def CTR_DRBG_Update(provided_data, Key, V):
    """Update Key and V using provided_data. See module docstring for rightmost() note."""
    ctr_len = 64
    blocklen = 128
    seedlen = 256
    keylen = 128
    temp = ''
    while ((len(temp)*4) < seedlen):
        if ctr_len < blocklen:
            inc = (int(rightmost(V, ctr_len), 16) + 1)% 2**ctr_len
            V = leftmost(V, blocklen-ctr_len) + bin_to_hex(format(inc, '0'+str(ctr_len)+'b'))
        else:
            V = (V+1)% 2**blocklen
        #print("VVVVVVVV", V)
        output_block = block_encrypt(Key, V)
        temp = temp + output_block
    temp = leftmost(temp, seedlen)
    temp = xor(temp, provided_data)
    Key = leftmost(temp, keylen)
    V = rightmost(temp, blocklen)
    return Key, V

def select(V, a, b):
    """Return bits from position a to b (inclusive) of hex string V."""
    V = hex_to_bin(V)
    substring = V[a:b]
    substring = bin_to_hex(substring)
    #print("SUBBBB", substring)
    return substring

def leftmost(V, a):
    """Return the leftmost 'a' bits of hex string V."""
    V = hex_to_bin(V)
    substring = V[:a]
    substring = bin_to_hex(substring)
    return substring

def rightmost(V, a):
    """Return bits from hex string V.

    WARNING (Known Bug - DO NOT FIX): V[:-a] returns the leftmost (len-a) bits,
    not the rightmost 'a' bits as per NIST spec (which would be V[-a:]).
    Both Generate and Regenerate use this consistently, so embedding/extraction
    round-trips work correctly. Changing this would break all existing stego images.
    """
    V = hex_to_bin(V)
    substring = V[:-a]
    substring = bin_to_hex(substring)
    return substring

def hex_to_bin(X):
    """Convert a hex string to a binary string (4 bits per hex digit)."""
    bin = ''
    for i in range(0, len(X)):
        bin = bin + format(int(X[i], 16), '04b')

    return bin

def bin_to_hex(X):
    """Convert a binary string to a hex string (4 bits per hex digit)."""
    hexa = ''
    i = 0
    while i<len(X):
        hexa = hexa + hex(int(X[i:i+4], 2))[2:]
        i = i + 4
    return hexa

def new_entropy():
    """Generate 32 bytes of fresh entropy as a hex string."""
    entropy = get_random_bytes(32)
    entropy = hex(int.from_bytes(entropy, 'big'))[2:]
    return entropy

def block_encrypt(Key, data):
    """Encrypt a single block using AES-128 in ECB mode."""
    if len(data)%16 != 0:
        data = data + '0'*(16 - len(data)%16)
    data = int(data[:32], 16)
    data = data.to_bytes(16, 'big')
    Key = int(Key[:32], 16)
    Key = Key.to_bytes(16, 'big')
    cipher = AES.new(Key, AES.MODE_ECB)
    msg = cipher.encrypt(data)
    msg = hex(int.from_bytes(msg, 'big'))
    encrypted_data = msg[2:]
    return encrypted_data

def xor(x, y):
    """XOR two hex strings and return the result as a binary string."""
    temp = len(x)
    x = int(x, 16)
    y = int(y, 16)
    xored = x^y
    #print('0'+str(temp)+'b')
    return format(int(hex(xored)[2:], 16),'0'+str(temp)+'b')

def split_random(X):
    """Split a hex string into an array of 32-bit unsigned integers."""
    split = []
    i = 0
    while i < len(X):
        split.append(int(X[i:i+8], 16))
        i = i + 8
    return np.array(split)

def main():
    import time
    start = time.time()
    entropy_input = '808182838485868788898A8B8C8D8E8F909192939495969798999A9B9C'
    nonce = '20212223242526'
    personalization_string = '404142434445464748494A4B4C4D4E4F505152535455565758595A5B5C'
    additional_input = ''
    security_strength = 128
    requested_number_of_bit = 512
    entropy_inputs = []
    V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, security_strength)
    for i in range(0, 10):
        returned_bits, Key, V, reseed_counter, entropy_inputs = CTR_DRBG_Generate(V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs)
        print(len(returned_bits))
        returned_bits = split_random(returned_bits)
        print("Resquested Bits:",(returned_bits))
    total_time = time.time() - start
    print("Total Time", total_time)
    print("entropy_inputs", len(entropy_inputs))

if __name__ == '__main__':
    main()
