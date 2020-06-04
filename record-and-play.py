from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

### TO DO:
### all .say should become a .play(), referencing a .wav that we will record ourselves
### NO robo-voices - only our voices
### probably polyphonic, like we did for that one conference that time?

### figure out how to:
### scale this up beyond a single Flask instance running off of a Mac in my house
### reliably store edited messages 

### build the logic behind 'listen' - how to serve people new messages?

### should we keep a log of past callers, so that it "remembers" them?  or is this a TERRIBLE idea? (kind of yes I believe so)

### should callers be able to navigate the messages?  how? sequential? random access?
### do we keep all messages up all the tiem or do we host one or two or three on a semi-regular (daily, weekly?) basis?
### editions...?

### WHEN YOU FIRST CALL

@app.route("/", methods=['GET','POST'])
def welcome():
	resp=VoiceResponse()
	# record a welcome
	resp.say("Leave a message in which you share your poetic observation or a selection of poetry to describe your experience at or during these uprisings with one caveat: Do so in just one breath.")
	gather=Gather(num_digits=1, action='/choice')
	gather.say("To listen to a message, please press 1.  To leave a message, please press 2.  To learn more about who we are, please press 3.")
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
				resp.say("I'm sorry, I don't understand.")
				resp.redirect('/')
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
	resp.say("First, state your first name and location.  Then take in one breath.  Speak your message only in one exhale.  Press the star key when you've finished recording.")
	### record the message - end 
	resp.record(maxlength=30, finishOnKey="*", trim="do-not-trim", action="/recordReview")
	### redirect to opportunity to review recording
	return str(resp)



@app.route("/recordReview", methods=['GET','POST'])
def recordReview():
	resp=VoiceResponse()
	entry = {}
	if 'RecordingUrl' in request.values:
		entry["recordFile"] = request.values['RecordingUrl']
		entry["callSid"] = request.values['CallSid']
		entry["recordingSid"] = request.values['RecordingSid']
		entry["recordingDuration"] = request.values["RecordingDuration"]
		with open("recording-files.txt","w") as log:
			log.write(entry["recordFile"])
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
		resp.say("We don't seem to have a recording.  This is an error on our part.  We'll do our best to fix it.")
		pass
	### play recording
	### -> retrieve + play recording
	resp.play(entry["recordFile"])
	### ask if they are happy with recording, and want to submit (log recording)
	gather=Gather(num_digits=1, action='/recordChoice')
	gather.say("To save this message, please press 1.  To re-record your message, please press 2.  To delete your recording and not re-record, please press the star key.")
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
			gather = Gather(num_digits=1, action="/choice")
			gather.say("To listen to messages that others have sent, please press 1.  If you're ready to go, please press the star key.")
			resp.append(gather)
		if selected == '2':
			### they want to re-record
			### -> delete old recording
			### RIGHT NOW ALL IT DOES IS NOT LOG THE RECORDING
			### NOT THE SAME - COULD CAUSE A PROBLEM LATER
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
	resp.say("Press star to hangup.")
	gather = Gather(num_digits=1, action="/listenChoice")
	gather.play("https://olive-wren-8959.twil.io/assets/onlyhaveeyes.mp3")
	resp.append(gather)
	### offer the option to:
	### A: listen to more messages
	### B: record your own message
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
	resp.say("LabSynthE (Laboratory for the Investigation of Synthetic and Electronic Poetry) is a platform for collaboration in the School of Arts, Technology, and Emerging Communication at UT Dallas. We are developing a new edition of our ongoing body of work, One Breath Poem, in which the voice is used to express a poem or poetic phrase with the limitation of speaking in just one “unit,” or a single breath. This edition is a call and response regarding the uprisings in response to police brutality and systemic racism in the summer of 2020.")
	gather = Gather(num_digits=1, action="/")
	gather.play("To listen to a message, please press 1.  To record a message, please press 2.  To hangup, please press the star key.")
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