from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import random

### DONE:
### all .say should become a .play(), referencing a .wav that we will record ourselves
### NO robo-voices - only our voices
### probably polyphonic, like we did for that one conference that time?

### TO DO:
### see if working audio is good, if not, normalize audio and reupload to twilio
### when uploading to twilio - USE SAME FILENAME

### definitely go through and have gather.play() refer to variables
### define those variables way up here at the top of the file
### that way we only have to change those variables, not play and hide and seek in this file

### plays in "/'"
introFile = "https://burgundy-toad-2613.twil.io/assets/INTRODUCTION-sean.mp3"
welcomeFile = "https://burgundy-toad-2613.twil.io/assets/WELCOME-xtine.wav"

### plays in "/record"
recordFile = "https://burgundy-toad-2613.twil.io/assets/RECORDING-sabrina.mp3"

# plays in "/recordReview" if no recording is found
errorFile = "https://burgundy-toad-2613.twil.io/assets/ERROR-leticia.mp3"

#plays in "/recordReview", prompt to save or toss recording
reviewFile = "https://burgundy-toad-2613.twil.io/assets/REVIEWING-cynthia.mp3"

# plays in "/recordChoice", prompt to listen to messages, record messages, or quit
choiceFile = "https://burgundy-toad-2613.twil.io/assets/LISTENINGTOMESSAGES-elmira.mp3"

# plays in "/listen", offering option to listen to more messages or record messages
listenFile = "https://burgundy-toad-2613.twil.io/assets/ABOUTUS2-maedeh.mp3"

# plays in "/aboutus", as intro to who LabSynthE is
aboutusFile = "https://burgundy-toad-2613.twil.io/assets/ABOUTUS-xtine.mp3"
# plays in "/aboutus", as prompt to make a choice
aboutchoiceFile = "https://burgundy-toad-2613.twil.io/assets/ABOUTUS2-maedeh.mp3"

### figured out how to:
### scale this up beyond a single Flask instance running off of a Mac in my house - 

### figure out how to:
### reliably store edited messages - is Twilio working OK for this?

### build the logic behind 'listen' - how to serve people new messages?

### should we keep a log of past callers, so that it "remembers" them?  or is this a TERRIBLE idea? (kind of yes I believe so)

### should callers be able to navigate the messages?  how? sequential? random access?
### do we keep all messages up all the tiem or do we host one or two or three on a semi-regular (daily, weekly?) basis?
### editions...?

# replace this with a function that automagically draws an approved message from an index of approved messages
recordedMessages = ["https://burgundy-toad-2613.twil.io/assets/06-07-20-fear-pride-anger.mp3","https://burgundy-toad-2613.twil.io/assets/06-04-20-solomon.mp3"]


#sets global timeout delay for gathers
gatherDelay = 10


app = Flask(__name__)


### WHEN YOU FIRST CALL

@app.route("/", methods=['GET','POST'])
def welcome():
	resp=VoiceResponse()
	# record a welcome
	resp.play(welcomeFile)
	gather = Gather(num_digits=1, action="/choice", timeout=gatherDelay)
	gather.play(introFile)
	resp.append(gather)
	resp.redirect('/choice')
	return str(resp)

### AFTER YOU DECIDE TO LISTEN OR RECORD - REDIRECTS YOUR CALL

@app.route("/choice", methods=['GET','POST'])
def choice():
		resp=VoiceResponse()
		if 'Digits' in request.values:
			selected = request.values['Digits']
			if selected == '1':
				resp.redirect('/listen')
			elif selected == '2':
				resp.redirect('/record')
			elif selected == '3':
				resp.redirect('/aboutus')
			elif selected == '*':
				resp.redirect('/goodbye')
			else:
				resp.redirect('/')
		else:
			resp.say("I'm sorry, there's an error.")
		return str(resp)

### RECORDING

@app.route("/record", methods=['GET','POST'])
def record():
	resp=VoiceResponse()
	### record the prompt -- should this recording 
	### a. happen in 3 parts? (1. name 2. location/relation 3. contribution), 
	### or 
	### b. each recording as a single file?
	### right now, this is structured as b. single recording.
	###
	### make sure to include, in recording of prompt, instructions that you can end recording by pressing *
	resp.play(recordFile)
	### record the message - end 
	resp.record(maxlength=30, finishOnKey="*", trim="do-not-trim", action="/recordReview")
	### redirect to opportunity to review recording
	return str(resp)



@app.route("/recordReview", methods=['GET','POST'])
def recordReview():
	resp=VoiceResponse()
	entry = {}
	if 'RecordingUrl' in request.values:
		entry["recordTemp"] = request.values['RecordingUrl']
		entry["callSid"] = request.values['CallSid']
		entry["recordingSid"] = request.values['RecordingSid']
		entry["recordingDuration"] = request.values["RecordingDuration"]
		with open("recording-files.txt","w") as log:
			log.write(entry["recordTemp"])
			log.write(",")
			log.write(entry["recordingSid"])
			log.write("\n")
			log.close()
		with open("TEMPrecording-logs.txt","w") as log:
			for x in entry.keys():
				log.write(entry[x])
				log.write("\n")
			log.close()
	else:
		resp.play(errorFile)
		pass
	### play recording
	### -> retrieve + play recording
	resp.play(entry["recordTemp"])
	### ask if they are happy with recording, and want to submit (log recording)
	gather=Gather(num_digits=1, action='/recordChoice', timeout=gatherDelay)
	gather.play(reviewFile)
	resp.append(gather)
	return str(resp)


@app.route("/recordChoice", methods=['GET','POST'])
def recordChoice():
	resp = VoiceResponse()
	entry=[]
	if 'Digits' in request.values:
		selected=request.values['Digits'] 
		if selected == '1':
			### -> log recording
			### -> log phone number they called from
			with open("TEMPrecording-logs.txt", "r") as log:
				for x in log.readlines():
					entry.append(x)
				log.close()
			with open("recording-logs.csv", "a") as log:
				tempWrite=""
				log.write("\n")
				for x in entry:
					tempWrite = tempWrite +","+x
				log.write(tempWrite)
				log.close()
			### ->-> this prevents people from filling our storage - either unintentionally or maliciously
			### ->-> include a function later to clear logged number once message has been approved or declined
			gather = Gather(num_digits=1, action="/choice", timeout=gatherDelay)
			gather.play(choiceFile)
			resp.append(gather)
		if selected == '2':
			### they want to re-record
			### -> delete old recording
			### RIGHT NOW ALL IT DOES IS NOT LOG THE RECORDING
			### NOT THE SAME - WILL CAUSE A PROBLEM LATER
			### ex. IF I KEEP CALLING AND CHOOSING TO 'RE-RECORD' OVER AND OVER AGAIN FOR A FEW HOURS
			### ex. I WILL CLOG THE STORAGE OF THE #
			### FIX THIS
			### -> redirect to /record 
			resp.redirect("/record")
		if selected == '*':
			### c. they want to delete and not re-record
			### read to hangup
			### FIX THIS - IT DOESN'T DELETE THE MESSAGE YET
			resp.redirect("/goodbye")
	return str(resp)


### LISTENING

@app.route("/listen", methods=['GET','POST'])
def listen():
	resp = VoiceResponse()
	### find a way to index & retrieve completed recordings
	### for now - referencing one of the recordings someone recorded to the GV with a random function
	listenMessage = random.choice(recordedMessages)
	resp.play(listenMessage)
	gather = Gather(num_digits=1, action="/listenChoice", timeout=gatherDelay)
	### maybe need to re-record this?
	### offer the option to:
	### A: listen to more messages
	### B: record your own message
	gather.play(listenFile)
	resp.append(gather)
	return str(resp)


@app.route("/listenChoice", methods=['GET','POST'])
def listenChoice():
	resp=VoiceResponse()
	if 'Digits' in request.values:
		selected = request.values['Digits'] 
		if selected == "*":
			resp.redirect("/goodbye")
		elif selected == "1":
			resp.redirect("/listen")
		else:
			resp.redirect("/")
	return str(resp) 


### ABOUT US

@app.route("/aboutus",methods=['GET','POST'])
def aboutUs():
	resp=VoiceResponse()
	resp.play(aboutusFile)
	gather = Gather(num_digits=1, action="/choice", timeout=gatherDelay)
	gather.play(aboutchoiceFile)
	resp.append(gather)

	return str(resp)

### GOODBYE

@app.route("/goodbye", methods=['GET','POST'])
def goodbye():
	resp = VoiceResponse()
	### an opportunity to say one final thing on the caller's way out the door, perform clean up actions, et c.
	resp.say("Thanks for calling.")
	resp.hangup()
	return str(resp)


if __name__ == "__main__":
	app.run()