import numpy as np
from cv2 import cv2
import imutils
import requests
from ffpyplayer.player import MediaPlayer

# url = "http://192.168.1.151:8080/shot.jpg"

cap = cv2.VideoCapture(0)
imgTarget = cv2.imread(r"C:\Users\shein\OneDrive\Desktop\New folder\Hello\unnamed.jpg")
myVid = cv2.VideoCapture(r"C:\Users\shein\OneDrive\Desktop\New folder\Hello\Heart.mp4")

detection = False
frameCounter =0

success, imgVideo = myVid.read()
hT, wT, cT = imgTarget.shape
imgVideo = cv2.resize(imgVideo, (wT, hT))

orb = cv2.ORB_create(nfeatures=1000) # detector
kp1, des1 = orb.detectAndCompute(imgTarget, None)
imgTarget = cv2.drawKeypoints(imgTarget,kp1,None)

def stackImages(imgArray,scale,lables=[]):
    sizeW= imgArray[0][0].shape[1]
    sizeH = imgArray[0][0].shape[0]
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv2.resize(imgArray[x][y], (sizeW,sizeH), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((sizeH, sizeW, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
            hor_con[x] = np.concatenate(imgArray[x])
        ver = np.vstack(hor)
        ver_con = np.concatenate(hor)
    else:
        for x in range(0, rows):
            imgArray[x] = cv2.resize(imgArray[x], (sizeW, sizeH), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        hor_con= np.concatenate(imgArray)
        ver = hor
    if len(lables) != 0:
        eachImgWidth= int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)
        print(eachImgHeight)
        for d in range(0, rows):
            for c in range (0,cols):
                cv2.rectangle(ver,(c*eachImgWidth,eachImgHeight*d),(c*eachImgWidth+len(lables[d])*13+27,30+eachImgHeight*d),(255,255,255),cv2.FILLED)
                cv2.putText(ver,lables[d],(eachImgWidth*c+10,eachImgHeight*d+20),cv2.FONT_HERSHEY_COMPLEX,0.7,(255,0,255),2)
    return ver

player = MediaPlayer(r"C:\Users\shein\OneDrive\Desktop\New folder\Hello\Heart.mp4")

while True:
    # img_resp = requests.get(url)
    # img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
    # imgWebcam = cv2.imdecode(img_arr, -1)
    # imgWebcam = cv2.resize(imgWebcam, (wT, hT))

    audio_frame, val = player.get_frame()
    
    success, imgWebcam = cap.read()
    imgAug = imgWebcam.copy()
    kp2, des2 = orb.detectAndCompute(imgWebcam, None)
    # imgWebcam = cv2.drawKeypoints(imgWebcam,kp2,None)

    # if val != 'eof' and audio_frame is not None:
    #         #audio
    #         img, t = audio_frame

    if detection==False:
        myVid.set(cv2.CAP_PROP_POS_FRAMES,0)
        frameCounter=0
    else:
        if frameCounter==myVid.get(cv2.CAP_PROP_FRAME_COUNT):
            myVid.set(cv2.CAP_PROP_POS_FRAMES,0)
            frameCounter=0
        success, imgVideo = myVid.read()
        imgVideo = cv2.resize(imgVideo, (wT, hT))

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)
    print(len(good))
    imgFeatures = cv2.drawMatches(imgTarget, kp1, imgWebcam, kp2, good, None, flags=2)

    if len(good)>25:
        detection = True
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
        matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        # print (matrix)

        pts = np.float32([ [0,0],[0,hT],[wT,hT],[wT,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,matrix)
        img2 = cv2.polylines(imgWebcam,[np.int32(dst)],True,(255,0,255),3, cv2.LINE_AA) # draw polylines

        imgWarp = cv2.warpPerspective(imgVideo, matrix, (img2.shape[1], img2.shape[0]))

        maskNew = np.zeros((imgWebcam.shape[0],imgWebcam.shape[1]),np.uint8) # create blank image of Augmentation size
        cv2.fillPoly(maskNew,[np.int32(dst)],(255,255,255)) # fill the detected area with white pixels to get mask
        maskInv = cv2.bitwise_not(maskNew) # get inverse mask
        imgAug = cv2.bitwise_and(imgAug, imgAug, mask=maskInv)
        imgAug = cv2.bitwise_or(imgWarp, imgAug)
        imgStacked = stackImages(([imgWebcam,imgTarget,imgVideo,imgFeatures],[imgWarp,maskNew,maskInv,imgAug]),0.5)
        
    audio_frame, val = player.get_frame()

    # timer = cv2.getTickCount()
    # fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
    # cv2.putText(imgAug,'FPS: {} '.format(int(fps)), (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (230,20,20), 3)
    cv2.putText(imgAug,'Target Found: {} '.format(detection), (25, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (230,20,20), 3)
    
    cv2.imshow('maskNew', imgAug)
    # cv2.imshow('imgWarp', imgWarp)
    # cv2.imshow('img2', img2)
    # cv2.imshow('imgTarget', imgTarget)
    # cv2.imshow('imgFeatures', imgFeatures)
    # cv2.imshow('myVid', imgVideo)
    cv2.imshow('myWebcam', imgWebcam)
    # cv2.imshow('imgStacked', imgStacked)
    cv2.waitKey(1)
    frameCounter += 1
