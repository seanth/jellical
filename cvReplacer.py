
import io,time,random,requests
from urllib.parse import urlparse

import cv2
from PIL import Image
import numpy
from slack import WebClient
from slack.errors import SlackApiError

testing = False
allowUpload = True
########################
#insert user token here
theToken3 = "" #user token
########################

##############
# Load the cascades
catface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalcatface.xml')
#catface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalcatface_extended.xml')
eye_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_eye.xml')
humanface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalface_default.xml')
##############

def pillow2GreyOpenCV(thePillowImg):
    numpyImage=numpy.array(thePillowImg) 
    openCVImage=cv2.cvtColor(numpyImage, cv2.COLOR_RGB2BGR) 
    # Convert into grayscale. Open CV needs the image to be greyscale
    greyOpenCVImg = cv2.cvtColor(openCVImage, cv2.COLOR_BGR2GRAY)
    return greyOpenCVImg
 

def replace(baseImg, pasteImg, theCoords, rotate="False"):
    for (x, y, w, h) in theCoords:
        print("             location: %s, %s" % (x,y))
        if type(rotate) == int:
            pasteImg = pasteImg.rotate(rotate)
        if rotate == "random":
            theRotation = random.randint(5, 355)
            pasteImg = pasteImg.rotate(theRotation)
        #adjust the superimposed head so it matches the found face size
        (hw,hh)=pasteImg.size
        widthRatio=hw/w
        print("               Ratio:: %s" % (widthRatio)) #print the ratio
        pasteImgResize = pasteImg.resize((w,int(hh/widthRatio)),Image.ANTIALIAS)
        #ok. put that head on there. Want a date?!
        baseImg.paste(pasteImgResize, (x,y), pasteImgResize)

    return baseImg

def replace_catHead(thePillowImg,theCoords):
    #baseImage = Image.open(imagePath)
    if testing == True:
        pasteImg = Image.open("heads/headtest.png")
    else:
        pasteImg = Image.open("heads/head1.png")
    # Draw rectangle around the facesw
    newImg = replace(thePillowImg, pasteImg, theCoords)
    return newImg

def replace_Eyes(thePillowImg,theCoords):
    #baseImage = Image.open(imagePath)
    if testing == True:
        pasteImg = Image.open("heads/headtest.png")
    else:
        pasteImg = Image.open("eyes/eye1.png")
    rotate = "random"
    # Draw rectangle around the facesw
    newImg = replace(thePillowImg, pasteImg, theCoords, rotate)
    return newImg

def replace_humanHead(thePillowImg,theCoords):
    #baseImage = Image.open(imagePath)
    if testing == True:
        pasteImg = Image.open("heads/headtest.png")
    else:
        pasteImg = Image.open("heads/head1.png")
    # Draw rectangle around the facesw
    newImg = replace(thePillowImg, pasteImg, theCoords)
    return newImg

def getImageUrl(imageUrl):
    parsedUrl = urlparse(imageUrl)
    if parsedUrl.netloc == "files.slack.com":
        theResponse = requests.get(imageUrl, headers={'Authorization': 'Bearer %s' % theToken3})   
    else:
        theResponse = requests.get(imageUrl)
    imageGet = (theResponse.content)
    #imagePath = io.BytesIO(imageGet.read())
    imagePath = io.BytesIO(imageGet)

def cvReplace(imagePath):
    replacementMade = False
    # Load the cascade
    catface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalcatface.xml')
    #catface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalcatface_extended.xml')
    eye_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_eye.xml')
    humanface_cascade = cv2.CascadeClassifier('harrcascades/haarcascade_frontalface_default.xml')

    #################
    #I split the retrieval of images out to it's own def
    # parsedUrl = urlparse(imageUrl)
    # if parsedUrl.netloc == "files.slack.com":
    #     theResponse = requests.get(imageUrl, headers={'Authorization': 'Bearer %s' % theToken3})   
    # else:
    #     theResponse = requests.get(imageUrl)
    # imageGet = (theResponse.content)
    # #imagePath = io.BytesIO(imageGet.read())
    # imagePath = io.BytesIO(imageGet)

    #pillow and opencv have slightly different ways of dealing with images
    #take the web image and make a pillow and opencv instance
    thePillowImg = Image.open(imagePath)                                    #pillow
    theOpenCVImg = cv2.cvtColor(numpy.array(thePillowImg), cv2.COLOR_RGB2BGR) #opencv

    # Convert into grayscale. Open CV needs the image to be greyscale
    greyOpenCVImg = cv2.cvtColor(theOpenCVImg, cv2.COLOR_BGR2GRAY)

    theEyes = eye_cascade.detectMultiScale(greyOpenCVImg, 1.1, 25)
    theCatFaces = catface_cascade.detectMultiScale(greyOpenCVImg, 1.1, 4)

    #Detect cat faces
    if type(theCatFaces).__module__==numpy.__name__:
        print("             I see a kitty!")
        thePillowImg = replace_catHead(thePillowImg, theCatFaces)
        #baseImage = Image.open(imagePath)
        replacementMade = True

    if replacementMade == False:
        if type(theEyes).__module__==numpy.__name__:
            print("             I see eyes!")
            thePillowImg = replace_Eyes(thePillowImg, theEyes)
            #baseImage = Image.open(imagePath)
            replacementMade = True

    if replacementMade:
        tempImgPath = "testaroo.png"#this should be the trinity hhmmdd--mmddyy
        print("             Saving tempfile: %s" % (tempImgPath))
        thePillowImg.save(tempImgPath,"PNG")

        if allowUpload:
            #let's see if we can upload an image to slack
            #mostly taken from https://pypi.org/project/slackclient/#uploading-files-to-slack
            ########################
            theChannel = "#jellical" #this is the name of the channel to target
            theToken = "" #bot token. NOT user token
            ########################
            client = WebClient(token=theToken)
            try:
                response = client.files_upload(channels=theChannel, file=tempImgPath)
                fileID= response["file"]["id"]
                print("     File ID: %s" % (fileID))
                assert response["file"]  # the uploaded file
                
                #if testing, delete the posted image
                if testing==True: 
                    time.sleep(5)
                    print("     Deleting file ID: %s" % (fileID))
                    client.files_delete(channels=theChannel, file=fileID)
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")
    else:
        print("nothing detected to change")
    return 










