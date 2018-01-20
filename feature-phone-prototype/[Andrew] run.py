"""Using Twilio's Python Quickstart guide, found at
https://www.twilio.com/docs/quickstart/python/twiml
"""

import time
import urllib

from flask import Flask, url_for, send_from_directory, request, redirect
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__, static_url_path='')


@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming requests."""
    resp = VoiceResponse()
    resp.say("Welcome to Malasakit.")
    resp.say("Here you will be asked several questions about typhoon preparedness.")
    resp.pause(1)
    resp.redirect(url_for('play_quant_question'))
    return str(resp)

@app.route('/mp3/<path:path>')
def send_mp3(path):
    print("asdf", path)
    return send_from_directory('mp3', path)

@app.route('/handle-recording', methods=['GET', 'POST'])
def handle_recording():
    resp = VoiceResponse()
    recording_url = request.values.get('RecordingUrl', None)
    user_response = urllib.URLopener()
    user_response.retrieve(recording_url, 'responses/response.mp3')
    resp.say("Response received.")
    resp.redirect(url_for('play_qual_question'))

    return str(resp)


@app.route('/handle-recording-qual', methods=['GET', 'POST'])
def handle_recording_qual():
    resp = VoiceResponse()
    recording_url = request.values.get('RecordingUrl', None)
    user_response = urllib.URLopener()
    user_response.retrieve(recording_url, 'responses/response_qual.mp3')
    resp.say("Response received.")
    resp.pause(1)
    resp.say("Thanks for participating in Malasakit.")
    resp.pause(0.5)
    return str(resp)

@app.route('/play-quant-question', methods=['GET','POST'])
def play_quant_question():
    resp = VoiceResponse()
    resp.say("Please answer Question %s by saying a number from 0 to 9." % 1)
    resp.play("%smp3/%s" % (request.url_root, 'q01.mp3'))
    resp.record(maxLength='1', action='/handle-recording')
    return str(resp)

@app.route('/play-qual-question', methods=['GET', 'POST'])
def play_qual_question():
    resp = VoiceResponse()
    resp.say("This is an open-ended question. You have up to 15 seconds to record a response.")
    resp.play("%smp3/%s" % (request.url_root, 'qual.mp3'))
    resp.record(maxLength='15', action='/handle-recording-qual')
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
