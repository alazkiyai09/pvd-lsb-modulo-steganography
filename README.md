<div align="center">

# PVD-LSB Modulo Steganography

### Improving the Imperceptibility of Pixel Value Difference and LSB Substitution Based Steganography Using Modulo Encoding

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy)](https://numpy.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv)](https://opencv.org/)
[![PyCryptodome](https://img.shields.io/badge/PyCryptodome-AES--128-green.svg)](https://pycryptodome.readthedocs.io/)
[![License](https://img.shields.io/badge/License-Academic-orange.svg)](#license)

[Overview](#-overview) • [Method](#-proposed-method) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Results](#-experiment-results) • [Citation](#-citation)

---

A research implementation of a **combined PVD + LSB steganography scheme** enhanced with **modulo encoding** and **CTR_DRBG key-dependent embedding** for improved imperceptibility in digital images.

**Published Research** • **3 Steganography Methods** • **131 Test Images** • **Comprehensive Experiments**

</div>

---

## Overview

This repository implements the steganographic method proposed in *"Improving the Imperceptibility of Pixel Value Difference and LSB Substitution Based Steganography Using Modulo Encoding"*. The core contribution is a **modulo encoding scheme** that distributes message data across two embedding channels — LSB substitution and PVD — to minimize visual distortion while maintaining capacity.

### Key Contributions

- **Modulo Encoding** — Splits each message hex digit into remainder (mod 8, 3 bits) and quotient (div 8, 1 bit), routing low-impact bits through LSB and high-impact bits through PVD
- **Key-Dependent Embedding** — Uses NIST SP 800-90A CTR_DRBG to generate position-dependent masks, making the embedding pattern unpredictable without the key
- **Channel Optimization** — Automatically selects the RGB channel with fewest boundary pixels (0 or 255) for PVD embedding to reduce distortion
- **Comparative Analysis** — Includes implementations of two baseline methods for experimental comparison

### Project Stats

| Metric | Detail |
|--------|--------|
| **Methods Implemented** | 3 (proposed + 2 baselines) |
| **Source Files** | 9 Python modules |
| **Test Images** | 131 (31 TIFF + 100 PNG) |
| **Message Sizes** | 10 per image |
| **Total Experiments** | 1,310 embedding trials |
| **Quality Metrics** | PSNR, MSE, SSIM |

---

## Proposed Method

### Embedding Pipeline

```
Input Message (hex)
        │
        ▼
┌─────────────────┐
│ Modulo Encoding  │  Split each hex digit: remainder = digit % 8, quotient = digit // 8
│  (mod 8 / div 8) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Remainder│ │Quotient│
│ (3 bit) │ │ (1 bit) │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌────────┐ ┌────────┐
│  LSB    │ │  PVD    │
│Embedding│ │Embedding│   Key K from CTR_DRBG
└───┬────┘ └───┬────┘   (position-dependent)
    │          │
    └────┬─────┘
         ▼
   ┌───────────┐
   │ Stego Image│
   └───────────┘
```

### How It Works

1. **Modulo Encoding**: Each hex character `h` of the message is split into `h % 8` (remainder, 0-7 = 3 bits) and `h // 8` (quotient, 0-1 = 1 bit)
2. **Key Generation**: CTR_DRBG (AES-128) generates pseudorandom keys `K` that change every 3 pixels, creating position-dependent masking
3. **LSB Embedding**: The 3-bit remainder is XORed with key-derived mask bits and embedded into the LSBs of three pixel channels (R, G, B)
4. **PVD Embedding**: The 1-bit quotient is embedded by modifying the pixel value difference between pixel pairs on the optimized channel, using key-dependent XOR
5. **Channel Optimization**: Before embedding, the algorithm selects the color channel with the fewest saturated pixels (0 or 255) to minimize out-of-bound cases

### Extraction

Extraction reverses the process using the same DRBG key sequence (via `CTR_DRBG_Regenerate`), recovering quotients from PVD differences and remainders from LSBs, then reconstructing the message via modulo decoding.

---

## Architecture

### File Structure

```
pvd-lsb-modulo-steganography/
├── CTR_DRBG.py                 # NIST SP 800-90A CTR_DRBG implementation
├── Final_Project_1.py          # Proposed method: PVD + LSB + Modulo Encoding
├── Experiment/
│   ├── CTR_DRBG.py             # (synced copy)
│   ├── Final_Project_1.py      # (synced copy)
│   ├── Previous_Method.py      # Baseline 1: Wu & Tsai PVD + LSB
│   ├── Previous_Method_2.py    # Baseline 2: MSLDIP + PVD
│   ├── Experiment.py           # Experiment runner — proposed method
│   ├── Experiment_P_1.py       # Experiment runner — baseline 1
│   ├── Experiment_P_2.py       # Experiment runner — baseline 2
│   └── *.xlsx                  # Experiment result spreadsheets
├── Reference/                  # Reference papers (PDF)
├── Draft Paper.docx            # Paper draft
└── *.pdf                       # Published paper
```

### Dependency Graph

```
CTR_DRBG.py ◄──── Final_Project_1.py ◄──── Experiment.py
                                              (Proposed Method)

Previous_Method.py ◄──── Experiment_P_1.py
  (Baseline 1)            (Wu & Tsai PVD+LSB)

Previous_Method_2.py ◄──── Experiment_P_2.py
  (Baseline 2)              (MSLDIP + PVD)
```

### Methods Compared

| # | Method | Technique | File |
|---|--------|-----------|------|
| 1 | **Proposed** | PVD + LSB + Modulo Encoding + CTR_DRBG | `Final_Project_1.py` |
| 2 | **Baseline 1** | Wu & Tsai PVD + LSB Substitution | `Previous_Method.py` |
| 3 | **Baseline 2** | MSLDIP + PVD with MPK Encoding | `Previous_Method_2.py` |

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.8+ |
| **Image Processing** | OpenCV, Pillow |
| **Numerical Computing** | NumPy, Pandas |
| **Cryptography** | PyCryptodome (AES-128-ECB for CTR_DRBG) |
| **Quality Metrics** | scikit-image (SSIM), scikit-learn (MSE) |
| **Visualization** | Matplotlib |

---

## Quick Start

### Prerequisites

```bash
pip install numpy opencv-python Pillow pycryptodome pandas scikit-image scikit-learn matplotlib
```

### Embedding a Message

```python
from Final_Project_1 import *
from CTR_DRBG import *

# DRBG setup
entropy_input = '808182838485868788898A8B8C8D8E8F909192939495969798999A9B9C'
nonce = '20212223242526'
personalization_string = '404142434445464748494A4B4C4D4E4F505152535455565758595A5B5C'
V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, 128)

# Read and encode message
M = read_file("Input.txt")
Rem, Div = modulo_encoding(M)
number_of_message = len(Div)

# Select optimal channel and embed
channel = optimizing("cover.png")
stego, metadata, entropy_inputs, out_of_bound = embedding_process(
    "cover.png", Rem, Div, V, Key, reseed_counter,
    512, '', [], number_of_message, channel
)

# Save stego image
cv2.imwrite("stego.tiff", stego)

# Save metadata (required for extraction)
save_metadata(metadata, entropy_input, nonce, personalization_string,
              entropy_inputs, number_of_message, out_of_bound, channel)
```

### Extracting a Message

```python
# Load metadata
entropy_input, nonce, personalization_string, entropy_inputs, \
    out_of_bound, number_of_message, pvd_parameter, channel = extract_metadata("Metadata2.txt")

# Re-instantiate DRBG with same parameters
V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, 128)

# Extract
Message = extraction_process(
    "stego.tiff", pvd_parameter, V, Key, reseed_counter,
    512, '', entropy_inputs, number_of_message, out_of_bound, channel
)
write_file("Output.txt", Message)
```

### Running the Full Experiment Suite

```bash
# Set base directory (default assumes original Windows paths)
export PAPERSTEGO_BASE_DIR="/path/to/your/data"

cd Experiment/

# Run proposed method experiments
python3 Experiment.py

# Run baseline comparisons
python3 Experiment_P_1.py   # Wu & Tsai PVD+LSB
python3 Experiment_P_2.py   # MSLDIP + PVD
```

---

## Experiment Results

### Quality Metrics

The proposed method is evaluated against two baselines across 131 cover images with 10 message sizes each.

| Metric | Description |
|--------|-------------|
| **PSNR** | Peak Signal-to-Noise Ratio (dB) — higher is better |
| **MSE** | Mean Squared Error — lower is better |
| **SSIM** | Structural Similarity Index — closer to 1 is better |

### Expected Results

The proposed method achieves **higher PSNR** and **lower MSE** compared to both baselines at equivalent embedding capacity, demonstrating improved imperceptibility through:
- Distributing embedding distortion across LSB and PVD channels via modulo encoding
- Reducing boundary pixel issues through channel optimization
- Key-dependent position masking that spreads modifications uniformly

Detailed results are available in the `Experiment/*.xlsx` spreadsheets.

---

## Known Limitations

| Issue | Description | Impact |
|-------|-------------|--------|
| **Metadata Side-Channel** | Embedding parameters stored in a separate file (`Metadata2.txt`) | Adversary discovering the file knows steganography was used |
| **NIST DRBG Deviation** | `rightmost()` returns leftmost bits instead of rightmost per NIST spec | Does not affect round-trip correctness; documented in code |
| **Fixed DRBG Parameters** | Entropy, nonce, and personalization string are hardcoded | Should be derived from a user-provided key in production use |
| **Out-of-Bound Threshold** | `extract_out_of_bound_pixel()` uses hardcoded threshold of 5 | Edge case at exactly P=5 is ambiguous |

See the full analysis in the [Research Concerns & Improvements](https://github.com/alazkiyai09/pvd-lsb-modulo-steganography/blob/main/README.md#known-limitations) section.

---

## References

1. Wu, D.C. and Tsai, W.H. — "A steganographic method for images by pixel-value differencing" (Pattern Recognition Letters, 2003)
2. NIST SP 800-90A — "Recommendation for Random Number Generation Using Deterministic Random Bit Generators" (2015)
3. Khodaei, M. and Faez, K. — "New adaptive steganographic method using least-significant-bit substitution and pixel-value differencing" (IET Image Processing, 2012)
4. Cheddad, A. et al. — "Digital image steganography: Survey and analysis of current methods" (Signal Processing, 2010)

---

## License

This project is provided for **academic and research purposes**. If you use this code in your research, please cite the original paper.

---

## Contact

<div align="center">

**Ahmad Whafa Azka Al Azkiyai**

**Fraud Detection & AI Security Specialist**

Steganography | Federated Learning Security | Adversarial ML

---

[![Website](https://img.shields.io/badge/Website-Visit-green.svg)](https://alazkiyai09.github.io/)
[![GitHub](https://img.shields.io/badge/GitHub-alazkiyai09-black.svg)](https://github.com/alazkiyai09)
[![Email](https://img.shields.io/badge/Email-Get_in_Touch-red.svg)](mailto:azka.alazkiyai@outlook.com)

</div>
