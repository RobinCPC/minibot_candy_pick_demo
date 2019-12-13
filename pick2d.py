# -*- coding: utf-8 -*-
"""Functions for 2d picking demo"""
import numpy as np
import cv2, PIL
from cv2 import aruco
import matplotlib.pyplot as plt
import time
import json

def savePicFromCam(filename, cam_id, width, height):
    # Todo: check save picture or not
    cap = cv2.VideoCapture(cam_id)
    # set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    frame = None
    if cap.isOpened():
        time.sleep(0.5)
        print("sleep 0.5")
        ret, frame = cap.read()
        cv2.imwrite(filename, frame)
        #img = img[:, 420:1500]
        #img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #plt.imsave(filename, img)
    else:
        print ("camera not detect.\n")
        return frame
    cap.release()
    return frame
    

def calibratePicture(filename, mark_id, mark_size):
    # read picture from file and pre-process
    frame = cv2.imread(filename)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # depend on source
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # detect aruco marker and draw on frame
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    parameters =  aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
    # find the marker we use for setting base
    corner1 = []
    for i in range(len(ids)):
        if ids[i] == mark_id:
            corner1 = corners[i][0]
            print corner1
    # compute transfer matrix according to the size of the marker
    pts1 = np.float32(corner1)
    pts2 = np.float32([ [0,0], [mark_size, 0], [mark_size, mark_size], [0, mark_size] ])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    frame_transform = cv2.warpPerspective(frame_markers, M, (mark_size, mark_size))
    plt.figure(figsize = (28,11))
    plt.subplot(121),plt.imshow(frame_markers),plt.title('Input')
    plt.subplot(122),plt.imshow(frame_transform),plt.title('Output')
    plt.show()
    return M


def do_inference(sage_client, endpoint_name, cv_frame, threshold=0.5):
    """
    Note: cv_frame its color channels are BGR used by opencv
    return prediction.
    """
    # encode image as jpeg
    _, img_encoded = cv2.imencode('.jpg', cv_frame)
    response = sage_client.invoke_endpoint(EndpointName=endpoint_name, 
                                   ContentType= 'image/jpeg', 
                                   Body=img_encoded.tostring())
    result = response['Body'].read()
    result = json.loads(result)
    print("Number of total predictions: ", len(result['prediction']))
    predictions = [prediction for prediction in result['prediction'] if prediction[1] > threshold]    
    return predictions


def make_predicted_image(img, predictions, class_list):
    """
    Note: img its color channels are RGB
    """
    n_classes = len(class_list)
    # Set the colors for the bounding boxes
    colors = plt.cm.rainbow(np.linspace(0, 1, n_classes+1)).tolist()

    imh, imw, _ = img.shape
    plt.figure(figsize=(20,12))
    plt.imshow(img)
    current_axis = plt.gca()

    for box in predictions:
        xmin = box[2] * imw
        ymin = box[3] * imh
        xmax = box[4] * imw
        ymax = box[5] * imh
        color = colors[int(box[0])]
        label = '{}: {:.2f}'.format(class_list[int(box[0])], box[1])
        current_axis.add_patch(plt.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin, color=color, fill=False, linewidth=2))  
        current_axis.text(xmin, ymin, label, size='x-large', color='black', bbox={'facecolor':color, 'alpha':1.0})
    return


"""
# check use picture or cam
cap = None
frame = None
if use_pic:
    frame = cv2.imread(filename)
else: # use cam
    frame = savePicFromCam(filename, cam_id, width, height)
pass
"""
