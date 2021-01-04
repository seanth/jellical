
import os, threading

import cv2
from flask import Flask, request, Response
from slack import WebClient
from slack.errors import SlackApiError
#############
import cvReplacer

app = Flask(__name__)

############################
theToken = ""
thisBotID = '' #the bot ID
############################


def eventHandler(eventType, slackEventJson):
    if eventType == 'message':
        print("        message posted")
        if 'subtype' in slackEventJson['event']:
            print("           there is a subtype")
            if slackEventJson['event']['subtype'] == 'message_deleted':
                print("           something was deleted")

            #this series of steps will identify if a file was uploaded, and what the
            #url is to get at the file
            if slackEventJson['event']['subtype'] == 'file_share':
                if 'files' in slackEventJson['event']:
                    theFiles = slackEventJson['event']['files']
                    if len(theFiles)>0:
                        imageInfo = theFiles[0]
                        theUser = imageInfo['user']
                        if theUser == thisBotID:
                            print("           Seems like I am seeing myself do something on slack. Ignore.")
                        else:
                            if 'url_private' in imageInfo:
                                theImageUrl = imageInfo['url_private']
                                print("           url_private: %s" % theImageUrl)
                                print("           Sending url for processing...")
                                cvReplacer.cvReplace(theImageUrl)

        #this series of steps will identify if a url was posted, and what the
        #url is to get at the file                    
        if 'message' in slackEventJson['event']:
            if 'attachments' in slackEventJson['event']['message']:
                theAttachments = slackEventJson['event']['message']['attachments']
                theUser = slackEventJson['event']['message']['user']
                if theUser == thisBotID:
                    print("           Seems like I am seeing myself do something on slack. Ignore.")
                else:
                    if len(theAttachments)>0:
                        imageInfo = theAttachments[0]
                        if 'original_url' in imageInfo:
                            theImageUrl = imageInfo['original_url']
                            print("           original url: %s" % theImageUrl)
                            print("           Sending url for processing...")
                            cvReplacer.cvReplace(theImageUrl)
                            #print(slackEventJson['event']['message']['attachments'])


@app.route('/slack', methods=['POST'])

def inbound():
    slackEventJson = request.json
    #print(slackEventJson)

    ###This is the initial authentication step that slack requires
    if ("challenge" in slackEventJson) and ("type" in slackEventJson):
        if (slackEventJson['type'] == "url_verification") and (slackEventJson['token'] == theToken):
            theChallenge = slackEventJson["challenge"]
            print("     Url verification request")
            print("       Challenge: %s" % theChallenge)
            theReturnText =  "challenge=%s" % theChallenge
            return Response(theReturnText), 200

    if (slackEventJson['token'] == theToken) and ("event" in slackEventJson):
        #print(slackEventJson)

        eventType = slackEventJson['event']['type']
        #eventHandler(eventType, slackEventJson)
        #########
        aThread = threading.Thread(target=eventHandler, args=(eventType,slackEventJson,))
        aThread.start()
        #########
        
        print("Returning 200")
        return Response(), 200

 
@app.route('/', methods=['GET'])
def test():
    print("bla")
    return Response('It works!')


if __name__ == "__main__":
    app.run(debug=True)