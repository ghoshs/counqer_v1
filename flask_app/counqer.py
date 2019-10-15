from flask import Flask, render_template, url_for, json, request, jsonify
from flask_cors import CORS, cross_origin
from get_count_data import related_predicate
try: 
	import urllib2 as myurllib
except ImportError:
	import urllib.request as myurllib

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# this is a comment
@app.route('/spoquery', methods=['GET', 'POST'])
@cross_origin()
def parse_request():
	option = request.args.get('option')
	subID = myurllib.unquote(request.args.get('subject'))
	objID = myurllib.unquote(request.args.get('object'))
	predID = request.args.get('predicate')
	print('counqer.py: L21: ', option, subID, predID, objID)
	# print(option, subID, predID)
	response = related_predicate(option, subID, predID, objID)
	# response = related_predicate(option, subID, predID)
	return jsonify(response)

@app.route('/')
@cross_origin()
def display_mainpage():
        #return "Hello World!"
	return render_template('index.html')

if __name__ == '__main__':
        #app.run()
	app.run(debug=True, port=5000)
