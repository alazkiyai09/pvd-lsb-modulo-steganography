import os
from Final_Project_1 import *
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
EXPERIMENT_DIR = os.path.join(BASE_DIR, 'Experiment', 'Experiment Proposed Method')
DATASET_DIR = os.path.join(BASE_DIR, 'Dataset')
NEW_DATASET_DIR = os.path.join(BASE_DIR, 'New Dataset')
MESSAGE_DIR = os.path.join(BASE_DIR, 'Experiment')


def embedding_experiment(path1, path2, index1, index2, channel):
    start = time.time()
    filename1 = path1
    filename2 = path2
    entropy_input = '808182838485868788898A8B8C8D8E8F909192939495969798999A9B9C'
    nonce = '20212223242526'
    personalization_string = '404142434445464748494A4B4C4D4E4F505152535455565758595A5B5C'
    additional_input = ''
    security_strength = 128
    requested_number_of_bit = 512
    entropy_inputs = []
    V, Key, reseed_counter = CTR_DRBG_Instantiate(entropy_input, nonce, personalization_string, security_strength)

    M = read_file(filename2)
    Rem, Div = modulo_encoding(M)
    number_of_message = len(Div)

    stego, metadata, entropy_inputs, out_of_bound = embedding_process(filename1, Rem, Div, V, Key, reseed_counter, requested_number_of_bit, additional_input, entropy_inputs, number_of_message, channel)
    exp_image_dir = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + index1)
    dir_stego = os.path.join(exp_image_dir, 'Stego' + index2 + '.tiff')
    cv2.imwrite(dir_stego, stego)
    calculate_hist(dir_stego, path1, index2, exp_image_dir)
    save_metadata(metadata, entropy_input, nonce, personalization_string, entropy_inputs, number_of_message, index1, index2, out_of_bound, channel)
    total_time = time.time() - start
    psnrs, mse = psnr(dir_stego, filename1)
    ssim_val = compute_ssim(dir_stego, filename1)

    data = ['Total Time: '+str(total_time),'PSNR: '+str(psnrs), 'MSE: '+str(mse), 'SSIM: '+str(ssim_val), 'Out of Bound Pixel: '+str(len(out_of_bound))]

    dir_data = os.path.join(exp_image_dir, 'Result' + index2 + '.txt')
    write_data(dir_data, data)

    filename = os.path.join(EXPERIMENT_DIR, 'Result Proposed Method.csv')
    csv_data = pd.read_csv(filename)
    new_row = pd.DataFrame([{"Image": "Image "+str(index1), "Message": "Message "+str(index2), "MSE": str(mse), "PSNR": str(psnrs), "SSIM": str(ssim_val), "Time": str(total_time), "Capacity":str(number_of_message*4), "Out of Bound": str(len(out_of_bound))}])
    csv_data = pd.concat([csv_data, new_row], ignore_index=True)
    csv_data.to_csv(filename, index=None)


def create_csv_file():
    filename = os.path.join(EXPERIMENT_DIR, 'Result Proposed Method.csv')
    newData = pd.DataFrame(columns=['Image','Message','MSE','PSNR','SSIM','Time', 'Capacity','Out of Bound'], index=None)
    newData.to_csv(filename, index=None)

def save_metadata(metadata, param1, param2, param3, param4, number_of_block, dir, dir2, out_of_bound, channel):
    temp = ''
    metadata1 = metadata_to_byte(metadata)
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
    meta_path = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + dir, 'Metadata' + dir2 + '.txt')
    write_file(meta_path, full_metadata)

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

def make_file():
    os.system('fsutil file createnew Input'+str(i+1)+'.txt '+ str(number_of_message))
    number_of_message = number_of_message + 11875

def write_data(dir, data):
    file1 = open(dir,"w")
    for i in range(0, len(data)):
        file1.write(data[i]+'\n')
    file1.close()

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


def main():
    create_csv_file()
    for i in range(0, 31):
        newpath = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + str(i+1))
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        dir = str(i+1)
        filename1 = os.path.join(DATASET_DIR, 'Image ' + str(i+1) + '.tiff')
        wide, high = Image.open(filename1).size
        channel = optimizing(filename1)
        print("Image "+dir+' Start')
        for j in range(0, 10):
            filename2 = os.path.join(MESSAGE_DIR, 'Message ' + str(wide), 'Input' + str(j+1) + '.txt')
            dir2 = str(j+1)
            embedding_experiment(filename1, filename2, dir, dir2, channel)
            print("Message "+dir2+' Complete')

        print("Image "+dir+' Complete')

    for i in range(0, 100):
            newpath = os.path.join(EXPERIMENT_DIR, 'Experiment Image ' + str(i+32))
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            dir = str(i+32)
            filename1 = os.path.join(NEW_DATASET_DIR, 'Image ' + str(i+32) + '.png')
            wide, high = Image.open(filename1).size
            channel = optimizing(filename1)
            print("Image "+dir+' Start')
            for j in range(0, 10):
                filename2 = os.path.join(MESSAGE_DIR, 'Message ' + str(wide), 'Input' + str(j+1) + '.txt')
                dir2 = str(j+1)
                embedding_experiment(filename1 ,filename2, dir, dir2, channel)
                print("Message "+dir2+' Complete')
            print("Image "+dir+' Complete')
if __name__ == '__main__':
    main()
