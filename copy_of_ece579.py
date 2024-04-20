# -*- coding: utf-8 -*-
"""Copy of ECE579.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/10VtZzCo4PxPWJNtaQgHKpzbXaOqltGDe

First we need to import/clone library for tensorflow object detection from github
"""

!pip uninstall Cython -y # Temporary fix for "No module named 'object_detection'" error
!git clone --depth 1 https://github.com/tensorflow/models

"""After we cloned tensoflow models library, we mainly will use the following official documentation to set up our environment for training: https://tensorflow-object-detection-api-tutorial.readthedocs.io/en/latest/training.html"""

# Commented out IPython magic to ensure Python compatibility.
# # Copy setup files into models/research folder
# %%bash
# cd models/research/
# protoc object_detection/protos/*.proto --python_out=.

# Modify setup.py file to install the tf-models-official repository targeted at TF v2.8.0
import re
with open('/content/models/research/object_detection/packages/tf2/setup.py') as f:
    s = f.read()

with open('/content/models/research/setup.py', 'w') as f:
    # Set fine_tune_checkpoint path
    s = re.sub('tf-models-official>=2.5.1',
               'tf-models-official==2.8.0', s)
    f.write(s)

# Install the Object Detection API

!pip install pyyaml==5.3
!pip install /content/models/research/

# Need to downgrade to TF v2.8.0 due to Colab compatibility bug with TF v2.10
!pip install tensorflow==2.8.0

# Install CUDA version 11.0 (to maintain compatibility with TF v2.8.0)
!pip install tensorflow_io==0.23.1
!wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-ubuntu1804.pin
!mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600
!wget http://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers/cuda-repo-ubuntu1804-11-0-local_11.0.2-450.51.05-1_amd64.deb
!dpkg -i cuda-repo-ubuntu1804-11-0-local_11.0.2-450.51.05-1_amd64.deb
!apt-key add /var/cuda-repo-ubuntu1804-11-0-local/7fa2af80.pub
!apt-get update && sudo apt-get install cuda-toolkit-11-0
!export LD_LIBRARY_PATH=/usr/local/cuda-11.0/lib64:$LD_LIBRARY_PATH

# Run Model Bulider Test file, just to verify everything's working properly
!python /content/models/research/object_detection/builders/model_builder_tf2_test.py

"""For the following section, we will prepare our data, in our case pre labeled images, I will use images stored in my google drive"""

# Copy from Google Drive
from google.colab import drive
drive.mount('/content/drive')

"""Create train, validation and test folders"""

!mkdir /content/images
!mkdir /content/images/train; mkdir /content/images/validation; mkdir /content/images/test; mkdir /content/images/all;

!cp -r /content/drive/MyDrive/Projects/ECE579/split_images/* /content/images/all

"""Now, we will split images to 80% train, 10% validation and 10% test"""

!wget https://raw.githubusercontent.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/master/util_scripts/train_val_test_split.py
!python train_val_test_split.py

"""Create label map for tensorflow training"""

# Commented out IPython magic to ensure Python compatibility.
# ### This creates a a "labelmap.txt" file with a list of classes the object detection model will detect.
# %%bash
# cat <<EOF >> /content/labelmap.txt
# crosswalk
# sidewalk
# signal_light_Please_Stop
# signal_light_Please_Walk
# EOF

"""Now that we have generated our annotations and split our dataset into the desired training and testing subsets, it is time to convert our annotations into the so called TFRecord format."""

# Download data conversion scripts
! wget https://raw.githubusercontent.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/master/util_scripts/create_csv.py
! wget https://raw.githubusercontent.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/master/util_scripts/create_tfrecord.py

# Create CSV data files and TFRecord files
!python3 create_csv.py
!python3 create_tfrecord.py --csv_input=images/train_labels.csv --labelmap=labelmap.txt --image_dir=images/train --output_path=train.tfrecord
!python3 create_tfrecord.py --csv_input=images/validation_labels.csv --labelmap=labelmap.txt --image_dir=images/validation --output_path=val.tfrecord

"""We will store the locations of tfrecord files as variables so we can access it in the future"""

train_record_fname = '/content/train.tfrecord'
val_record_fname = '/content/val.tfrecord'
label_map_pbtxt_fname = '/content/labelmap.pbtxt'

"""Now we wneed to download our model that we will use for training, we will chose it from Tensorflow2 Detection Model Zoo: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md"""

# Commented out IPython magic to ensure Python compatibility.
# Create "mymodel" folder for holding pre-trained weights and configuration files
# %mkdir /content/models/mymodel/
# %cd /content/models/mymodel/

"""The model we shall be using in our examples is the SSD ResNet50 V1 FPN 640x640 model, since it provides a relatively good trade-off between performance and speed."""

# Change the chosen_model variable to deploy different models available in the TF2 object detection zoo
chosen_model = 'ssd-mobilenet-v2-fpnlite-320'

MODELS_CONFIG = {
    'ssd-mobilenet-v2': {
        'model_name': 'ssd_mobilenet_v2_320x320_coco17_tpu-8',
        'base_pipeline_file': 'ssd_mobilenet_v2_320x320_coco17_tpu-8.config',
        'pretrained_checkpoint': 'ssd_mobilenet_v2_320x320_coco17_tpu-8.tar.gz',
    },
    'efficientdet-d0': {
        'model_name': 'efficientdet_d0_coco17_tpu-32',
        'base_pipeline_file': 'ssd_efficientdet_d0_512x512_coco17_tpu-8.config',
        'pretrained_checkpoint': 'efficientdet_d0_coco17_tpu-32.tar.gz',
    },
    'ssd-mobilenet-v2-fpnlite-320': {
        'model_name': 'ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8',
        'base_pipeline_file': 'ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.config',
        'pretrained_checkpoint': 'ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.tar.gz',
    },
    # The centernet model isn't working as of 9/10/22
    #'centernet-mobilenet-v2': {
    #    'model_name': 'centernet_mobilenetv2fpn_512x512_coco17_od',
    #    'base_pipeline_file': 'pipeline.config',
    #    'pretrained_checkpoint': 'centernet_mobilenetv2fpn_512x512_coco17_od.tar.gz',
    #}
}

model_name = MODELS_CONFIG[chosen_model]['model_name']
pretrained_checkpoint = MODELS_CONFIG[chosen_model]['pretrained_checkpoint']
base_pipeline_file = MODELS_CONFIG[chosen_model]['base_pipeline_file']

# Commented out IPython magic to ensure Python compatibility.
# Create "mymodel" folder for holding pre-trained weights and configuration files
# %mkdir /content/models/mymodel/
# %cd /content/models/mymodel/

# Download pre-trained model weights
import tarfile
download_tar = 'http://download.tensorflow.org/models/object_detection/tf2/20200711/' + pretrained_checkpoint
!wget {download_tar}
tar = tarfile.open(pretrained_checkpoint)
tar.extractall()
tar.close()

# Download training configuration file for model
download_config = 'https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/configs/tf2/' + base_pipeline_file
!wget {download_config}

# Set training parameters for the model
num_steps = 5000

batch_size = 32

# Set file locations and get number of classes for config file
pipeline_fname = '/content/models/mymodel/' + base_pipeline_file
fine_tune_checkpoint = '/content/models/mymodel/' + model_name + '/checkpoint/ckpt-0'

def get_num_classes(pbtxt_fname):
    from object_detection.utils import label_map_util
    label_map = label_map_util.load_labelmap(pbtxt_fname)
    categories = label_map_util.convert_label_map_to_categories(
        label_map, max_num_classes=90, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)
    return len(category_index.keys())
num_classes = get_num_classes(label_map_pbtxt_fname)
print('Total classes:', num_classes)

# Commented out IPython magic to ensure Python compatibility.
# Create custom configuration file by writing the dataset, model checkpoint, and training parameters into the base pipeline file
import re

# %cd /content/models/mymodel
print('writing custom configuration file')

with open(pipeline_fname) as f:
    s = f.read()
with open('pipeline_file.config', 'w') as f:

    # Set fine_tune_checkpoint path
    s = re.sub('fine_tune_checkpoint: ".*?"',
               'fine_tune_checkpoint: "{}"'.format(fine_tune_checkpoint), s)

    # Set tfrecord files for train and test datasets
    s = re.sub(
        '(input_path: ".*?)(PATH_TO_BE_CONFIGURED/train)(.*?")', 'input_path: "{}"'.format(train_record_fname), s)
    s = re.sub(
        '(input_path: ".*?)(PATH_TO_BE_CONFIGURED/val)(.*?")', 'input_path: "{}"'.format(val_record_fname), s)

    # Set label_map_path
    s = re.sub(
        'label_map_path: ".*?"', 'label_map_path: "{}"'.format(label_map_pbtxt_fname), s)

    # Set batch_size
    s = re.sub('batch_size: [0-9]+',
               'batch_size: {}'.format(batch_size), s)

    # Set training steps, num_steps
    s = re.sub('num_steps: [0-9]+',
               'num_steps: {}'.format(num_steps), s)

    # Set number of classes num_classes
    s = re.sub('num_classes: [0-9]+',
               'num_classes: {}'.format(num_classes), s)

    # Change fine-tune checkpoint type from "classification" to "detection"
    s = re.sub(
        'fine_tune_checkpoint_type: "classification"', 'fine_tune_checkpoint_type: "{}"'.format('detection'), s)

    # If using ssd-mobilenet-v2, reduce learning rate (because it's too high in the default config file)
    if chosen_model == 'ssd-mobilenet-v2':
      s = re.sub('learning_rate_base: .8',
                 'learning_rate_base: .08', s)

      s = re.sub('warmup_learning_rate: 0.13333',
                 'warmup_learning_rate: .026666', s)

    # If using efficientdet-d0, use fixed_shape_resizer instead of keep_aspect_ratio_resizer (because it isn't supported by TFLite)
    if chosen_model == 'efficientdet-d0':
      s = re.sub('keep_aspect_ratio_resizer', 'fixed_shape_resizer', s)
      s = re.sub('pad_to_max_dimension: true', '', s)
      s = re.sub('min_dimension', 'height', s)
      s = re.sub('max_dimension', 'width', s)

    f.write(s)

# Set the path to the custom config file and the directory to store training checkpoints in
pipeline_file = '/content/models/mymodel/pipeline_file.config'
model_dir = '/content/training/'

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard
# %tensorboard --logdir '/content/training/train'

# Run training!
!python /content/models/research/object_detection/model_main_tf2.py \
    --pipeline_config_path={pipeline_file} \
    --model_dir={model_dir} \
    --alsologtostderr \
    --num_train_steps={num_steps} \
    --sample_1_of_n_eval_examples=1

# Make a directory to store the trained TFLite model
!mkdir /content/custom_model_lite
output_directory = '/content/custom_model_lite'

# Path to training directory (the conversion script automatically chooses the highest checkpoint file)
last_model_path = '/content/training'

!python /content/models/research/object_detection/export_tflite_graph_tf2.py \
    --trained_checkpoint_dir {last_model_path} \
    --output_directory {output_directory} \
    --pipeline_config_path {pipeline_file}

# Convert exported graph file into TFLite model file
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_saved_model('/content/custom_model_lite/saved_model')
tflite_model = converter.convert()

with open('/content/custom_model_lite/detect.tflite', 'wb') as f:
  f.write(tflite_model)

!rm -r /content/sample_data

# Commented out IPython magic to ensure Python compatibility.
# Move labelmap and pipeline config files into TFLite model folder and zip it up
!cp /content/labelmap.txt /content/custom_model_lite
!cp /content/labelmap.pbtxt /content/custom_model_lite
!cp /content/models/mymodel/pipeline_file.config /content/custom_model_lite

# %cd /content
!zip -r custom_model_lite.zip custom_model_lite

from google.colab import files

files.download('/content/custom_model_lite.zip')

!mkdir /content/images/inference

!cp -r /content/drive/MyDrive/Projects/ECE579/split_test_images/* /content/images/inference/

# Commented out IPython magic to ensure Python compatibility.
# Script to run custom TFLite model on test images to detect objects
# Source: https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/blob/master/TFLite_detection_image.py

# Import packages
import os
import cv2
import numpy as np
import sys
import glob
import random
import importlib.util
from tensorflow.lite.python.interpreter import Interpreter

import matplotlib
import matplotlib.pyplot as plt

# %matplotlib inline

def tflite_detect_images_old(modelpath, imgfolder, lblpath, min_conf=0.5, savepath='/content/results'):
    # Load the label map into memory
    with open(lblpath, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Load the Tensorflow Lite model into memory
    interpreter = Interpreter(model_path=modelpath)
    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    float_input = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Loop over every image in the folder and perform detection
    for image_path in glob.glob(os.path.join(imgfolder, '*')):
        # Load image and resize to expected shape [1xHxWx3]
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        imH, imW, _ = image.shape
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if float_input:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Retrieve detection results
        boxes = interpreter.get_tensor(output_details[1]['index'])[0]  # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[3]['index'])[0]  # Class index of detected objects
        scores = interpreter.get_tensor(output_details[0]['index'])[0]  # Confidence of detected objects

        detections = []

        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > min_conf) and (scores[i] <= 1.0)):
                # Get bounding box coordinates and draw box
                ymin = int(max(1, (boxes[i][0] * imH)))
                xmin = int(max(1, (boxes[i][1] * imW)))
                ymax = int(min(imH, (boxes[i][2] * imH)))
                xmax = int(min(imW, (boxes[i][3] * imW)))

                # Draw rectangle and label
                cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)
                object_name = labels[int(classes[i])]
                label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                label_ymin = max(ymin, labelSize[1] + 10)
                cv2.rectangle(image, (xmin, label_ymin - labelSize[1] - 10), (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
                cv2.putText(image, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

                detections.append([object_name, scores[i], xmin, ymin, xmax, ymax])

        # Save detection results as PNG
        image_fn = os.path.basename(image_path)
        base_fn, ext = os.path.splitext(image_fn)
        png_result_fn = base_fn + '.png'
        png_savepath = os.path.join(savepath, png_result_fn)
        cv2.imwrite(png_savepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

# Set up variables for running user's model
PATH_TO_IMAGES='/content/images/inference'   # Path to test images folder
PATH_TO_MODEL='/content/custom_model_lite/detect.tflite'   # Path to .tflite model file
PATH_TO_LABELS='/content/labelmap.txt'   # Path to labelmap.txt file
min_conf_threshold = 0.3   # Confidence threshold (try changing this to 0.01 if you don't see any detection results)
images_to_test = 500   # Number of images to run detection on

# Run inferencing function!
tflite_detect_images(PATH_TO_MODEL, PATH_TO_IMAGES, PATH_TO_LABELS, min_conf_threshold)

!mkdir /content/results

# Commented out IPython magic to ensure Python compatibility.
# %cd /content
!zip -r results.zip results

# Copy from Google Drive
from google.colab import drive
drive.mount('/content/drive')

!cp -r /content/drive/MyDrive/Projects/ECE579/custom_model_lite /content

!mkdir /content/images

!mkdir /content/results

!mkdir /content/images/test

!cp -r /content/drive/MyDrive/Projects/ECE579/test_images_3/* /content/images/test

!cp -r /content/drive/MyDrive/Projects/ECE579/triangulation.py /content
!cp -r /content/drive/MyDrive/Projects/ECE579/calibration.py /content
!cp -r /content/drive/MyDrive/Projects/ECE579/stereoMap.xml /content

# Commented out IPython magic to ensure Python compatibility.
# Script to run custom TFLite model on test images to detect objects
# Source: https://github.com/EdjeElectronics/TensorFlow-Lite-Object-Detection-on-Android-and-Raspberry-Pi/blob/master/TFLite_detection_image.py

# Import packages
import os
import cv2
import numpy as np
import sys
import glob
import random
import importlib.util
from tensorflow.lite.python.interpreter import Interpreter
import math, time

import matplotlib
import matplotlib.pyplot as plt

# Function for stereo vision and depth estimation
import triangulation as tri
import calibration



# %matplotlib inline

def tflite_detect_boxes(read_image, image_path, modelpath = '/content/custom_model_lite/detect.tflite', lblpath = '/content/custom_model_lite/labelmap.txt', min_conf=0.25):
    # print('start detect boxes')
    # Load the label map into memory
    with open(lblpath, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Load the Tensorflow Lite model into memory
    interpreter = Interpreter(model_path=modelpath)
    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    float_input = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Load image and resize to expected shape [1xHxWx3]
    image = read_image
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    imH, imW, _ = image.shape
    image_resized = cv2.resize(image_rgb, (width, height))
    input_data = np.expand_dims(image_resized, axis=0)

    # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
    if float_input:
        input_data = (np.float32(input_data) - input_mean) / input_std

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[1]['index'])[0]  # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[3]['index'])[0]  # Class index of detected objects
    scores = interpreter.get_tensor(output_details[0]['index'])[0]  # Confidence of detected objects

    detections = []

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    # print('pre for')
    for i in range(len(scores)):
        if ((scores[i] > min_conf) and (scores[i] <= 1.0)):
            # Get bounding box coordinates and draw box
            ymin = int(max(1, (boxes[i][0] * imH)))
            xmin = int(max(1, (boxes[i][1] * imW)))
            ymax = int(min(imH, (boxes[i][2] * imH)))
            xmax = int(min(imW, (boxes[i][3] * imW)))

            object_name = labels[int(classes[i])]

            if object_name == "signal_light_Please_Stop" or object_name == "signal_light_Please_Walk":

              coordinates = [xmax, xmin, ymax, ymin]
              # print(coordinates)
              return coordinates
    return None

def get_depth(point_right, point_left, frame_right, frame_left):
    # Stereo vision setup parameters
    B = 8.5               #Distance between the cameras [cm]
    f = 4.2              #Camera lense's focal length [mm]
    alpha = 54        #Camera field of view in the horisontal plane [degrees]
    depth = tri.find_depth(point_right, point_left, frame_right, frame_left, B, f, alpha)
    return depth

def tflite_detect_images(modelpath, imgfolder, lblpath, min_conf=0.5, savepath='/content/results'):
    # Load the label map into memory
    with open(lblpath, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Load the Tensorflow Lite model into memory
    interpreter = Interpreter(model_path=modelpath)
    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    float_input = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Loop over every image in the folder and perform detection
    for image_path in glob.glob(os.path.join(imgfolder, '*')):
        # Load image and resize to expected shape [1xHxWx3]

  # ---------------------------------------
        #Stereo image processing
        # Load the stereo image
        stereo_image = cv2.imread(image_path)

        # Get the dimensions of the stereo image
        height_stereo, width_stereo, _ = stereo_image.shape

        read_image = cv2.imread(image_path)
        image  = read_image[:, 0:width_stereo//2]

        # Split the stereo image into left and right frames
        frame_left = stereo_image[:, 0:width_stereo//2]
        frame_right = stereo_image[:, width_stereo//2:]

        frame_right, frame_left = calibration.undistortRectify(frame_right, frame_left)

        left_box = tflite_detect_boxes(frame_left, image_path)
        right_box = tflite_detect_boxes(frame_right, image_path)



# ---------------------------------------------------
        # image = frame_right
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        imH, imW, _ = image.shape
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if float_input:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Retrieve detection results
        boxes = interpreter.get_tensor(output_details[1]['index'])[0]  # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[3]['index'])[0]  # Class index of detected objects
        scores = interpreter.get_tensor(output_details[0]['index'])[0]  # Confidence of detected objects

        detections = []

        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > min_conf) and (scores[i] <= 1.0)):
                # Get bounding box coordinates and draw box
                ymin = int(max(1, (boxes[i][0] * imH)))
                xmin = int(max(1, (boxes[i][1] * imW)))
                ymax = int(min(imH, (boxes[i][2] * imH)))
                xmax = int(min(imW, (boxes[i][3] * imW)))

                # Draw rectangle and label
                cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)
                object_name = labels[int(classes[i])]

                label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                label_ymin = max(ymin, labelSize[1] + 10)
                cv2.rectangle(image, (xmin, label_ymin - labelSize[1] - 10), (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
                cv2.putText(image, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

                detections.append([object_name, scores[i], xmin, ymin, xmax, ymax])

                # -------------------------------------------------------
                if left_box and right_box:
                    x_mid_left = (left_box[0] - left_box[1])/2
                    y_mid_left = (left_box[2] - left_box[3])/2
                    x_mid_right = (right_box[0] - right_box[1])/2
                    y_mid_right = (right_box[2] - right_box[3])/2
                    # print(left_box)
                    # print(right_box)
                    min_depth = 100000
                    for i in range(0, 11):
                        left_point = [x_mid_left - 5 + i + left_box[1], y_mid_left + left_box[3]]
                        right_point = [x_mid_right - 5 + i + right_box[1], y_mid_right + right_box[3]]
                        # print(left_point)
                        # print(right_point)
                        depth = get_depth(right_point, left_point, frame_right, frame_left)
                        if depth < 0:
                          depth = depth * -1
                        # print(depth)
                        if not math.isinf(depth) or depth != 0:
                            if depth < min_depth:
                              min_depth = depth
                    cv2.putText(image, "Distance: " + str(round(min_depth,1)), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                # --------------------------------------------------------

        # Save detection results as PNG
        image_fn = os.path.basename(image_path)
        base_fn, ext = os.path.splitext(image_fn)
        png_result_fn = base_fn + '.png'
        png_savepath = os.path.join(savepath, png_result_fn)
        # cv2.imwrite(png_savepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(png_savepath, image)

from google.colab import drive
drive.mount('/content/drive')

# Set up variables for running user's model
PATH_TO_IMAGES='/content/images/test'   # Path to test images folder
PATH_TO_MODEL='/content/custom_model_lite/detect.tflite'   # Path to .tflite model file
PATH_TO_LABELS='/content/custom_model_lite/labelmap.txt'   # Path to labelmap.txt file
min_conf_threshold = 0.25   # Confidence threshold (try changing this to 0.01 if you don't see any detection results)
images_to_test = 50   # Number of images to run detection on

# Run inferencing function!
tflite_detect_images(PATH_TO_MODEL, PATH_TO_IMAGES, PATH_TO_LABELS, min_conf_threshold)

!rm -r /content/images/test/*

!rm -r /content/results/*

# Commented out IPython magic to ensure Python compatibility.
# %cd /content
!zip -r results.zip results

!cp -r /content/results.zip /content/drive/MyDrive/Projects/ECE579

import shutil
import os
import glob

# Source directory
source_dir = '/content/drive/MyDrive/Projects/ECE579/test_images_stereo/'

# Destination directory
destination_dir = '/content/images/test/'

# List all files in the source directory
file_list = sorted(glob.glob(source_dir + '*'))

# Copy the first 25 images
for i, file_path in enumerate(file_list):
    if i < 25:
        file_name = os.path.basename(file_path)
        shutil.copy(file_path, os.path.join(destination_dir, file_name))
    else:
        break