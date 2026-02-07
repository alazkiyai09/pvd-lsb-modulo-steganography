from Previous_Method_2 import *
import os
import numpy
import math
import cv2
import pandas as pd
from sklearn.metrics import mean_squared_error
from skimage.metrics import structural_similarity as ssim
from PIL import Image

# --- Configurable base directory (change this to match your environment) ---
BASE_DIR = os.environ.get(
    'PAPERSTEGO_BASE_DIR',
    os.path.join('E:', os.sep, 'Lecture', 'Penulisan Proposal', 'Final Project')
)
EXPERIMENT_DIR = os.path.join(BASE_DIR, 'Experiment', 'Experiment Previous Method 2')
DATASET_DIR = os.path.join(BASE_DIR, 'Dataset')
NEW_DATASET_DIR = os.path.join(BASE_DIR, 'New Dataset')
MESSAGE_DIR = os.path.join(BASE_DIR, 'Experiment')


def file_size(filename):
    with open(filename, 'rb') as f:
        hexdata = f.read().hex()
    return hexdata

def calculate_hist(filename1, filename2, index, path):
    image1 = cv2.imread(filename2)
    hist1 = np.array([0]*256)
    hist1 = hist1.reshape(-1, 1)
    for i, col in enumerate(['b', 'g', 'r']):
        hist1 = hist1 + cv2.calcHist([image1], [i], None, [256], [0, 256])

    image2 = cv2.imread(filename1)
    hist2 = np.array([0]*256)
    hist2 = hist2.reshape(-1, 1)
    for i, col in enumerate(['b', 'g', 'r']):
        hist2 = hist2 + cv2.calcHist([image2], [i], None, [256], [0, 256])

    plt.plot(hist1, color = 'r', alpha=1, label='Cover', lw=0.75)
    plt.plot(hist2, color = 'b', alpha=0.5, label='Stego', lw=0.75)
    plt.xlim([0, 256])
    plt.legend()
    filename = os.path.join(path, "Stego " + str(index) + "(Histogram).png")
    plt.savefig(filename, dpi=1024)
    plt.close()
    hist1 = hist1.ravel()
    hist2 = hist2.ravel()

def write_data(dir, data):
    file1 = open(dir,"w")
    for i in range(0, len(data)):
        file1.write(data[i]+'\n')
    file1.close()

def psnr(img1, img2):
    original = cv2.imread(img1)
    stego = cv2.imread(img2)
    mse = numpy.mean( (original - stego) ** 2 )
    PIXEL_MAX = 255.0
    return 10*math.log10(PIXEL_MAX**2 / (mse)), mse

def compute_ssim(img1, img2):
    """Compute SSIM between two images."""
    original = cv2.imread(img1, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(img2, cv2.IMREAD_GRAYSCALE)
    return ssim(original, stego)

def create_csv_file():
    filename = os.path.join(EXPERIMENT_DIR, 'Result Previous Method 2.csv')
    newData = pd.DataFrame(columns=['Image','Message','MSE','PSNR','SSIM','Time', 'Capacity', 'Out of Bound'], index=None)
    newData.to_csv(filename, index=None)

def embedding_experiment(filename1, filename2, index1, index2):
    start = time.time()
    M = read_file(filename2)
    M = mpk_encoding(M)
    number_of_message = len(file_size(filename2))

    out_of_bound = 0

    cover = cv2.imread(filename1)
    cover_rgb = cv2.cvtColor(cover, cv2.COLOR_BGR2RGB)
    wide, high = Image.open(filename1).size
    cover_rgb = cover_rgb.reshape(wide*high*3, 1)
    j = 0
    i = 0
    while (i < len(M) - 1):
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

        if Pi < 0 or Pi > 255:
            out_of_bound = out_of_bound + 1
        elif Px < 0 or Px > 255:
            out_of_bound = out_of_bound + 1
        j = j + 2

    exp_image_dir = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + index1)
    dir_stego = os.path.join(exp_image_dir, 'Stego' + index2 + '.tiff')
    stego = cover_rgb.reshape(high, wide, 3)
    stego = cv2.cvtColor(stego, cv2.COLOR_RGB2BGR)
    cv2.imwrite(dir_stego, stego)
    total_time = time.time() - start

    calculate_hist(dir_stego, filename1, index2, exp_image_dir)

    psnrs, mse = psnr(dir_stego, filename1)
    ssim_val = compute_ssim(dir_stego, filename1)

    data = ['Total Time: '+str(total_time),'PSNR: '+str(psnrs), 'MSE: '+str(mse), 'SSIM: '+str(ssim_val), 'Out of Bound: '+str(out_of_bound)]

    dir_data = os.path.join(exp_image_dir, 'Result' + index2 + '.txt')
    write_data(dir_data, data)

    filename = os.path.join(EXPERIMENT_DIR, 'Result Previous Method 2.csv')
    csv_data = pd.read_csv(filename)
    new_row = pd.DataFrame([{"Image": "Image "+str(index1), "Message": "Message "+str(index2), "MSE": str(mse), "PSNR": str(psnrs), "SSIM": str(ssim_val), "Time": str(total_time), "Capacity":str(number_of_message*4), "Out of Bound":str(out_of_bound)}])
    csv_data = pd.concat([csv_data, new_row], ignore_index=True)
    csv_data.to_csv(filename, index=None)


def main():
    create_csv_file()
    for i in range(0, 31):
        newpath = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + str(i+1))
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        dir = str(i+1)
        filename1 = os.path.join(DATASET_DIR, 'Image ' + str(i+1) + '.tiff')
        wide, high = Image.open(filename1).size
        print("Image "+dir+' Start')
        for j in range(0, 10):
            filename2 = os.path.join(MESSAGE_DIR, 'Message ' + str(wide), 'Input' + str(j+1) + '.txt')
            dir2 = str(j+1)
            embedding_experiment(filename1, filename2, dir, dir2)
            print("Message "+dir2+' Complete')

        print("Image "+dir+' Complete')

    for i in range(0, 100):
            newpath = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + str(i+32))
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            dir = str(i+32)
            filename1 = os.path.join(NEW_DATASET_DIR, 'Image ' + str(i+32) + '.png')
            wide, high = Image.open(filename1).size
            print("Image "+dir+' Start')
            for j in range(0, 10):
                filename2 = os.path.join(MESSAGE_DIR, 'Message ' + str(wide), 'Input' + str(j+1) + '.txt')
                dir2 = str(j+1)
                embedding_experiment(filename1 ,filename2, dir, dir2)
                print("Message "+dir2+' Complete')
            print("Image "+dir+' Complete')
if __name__ == '__main__':
    main()
