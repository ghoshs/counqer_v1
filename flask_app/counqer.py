from flask import Flask, render_template, url_for, json, request, jsonify
from flask_cors import CORS, cross_origin
from get_count_data import related_predicate
import urllib

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# this is a comment
@app.route('/spoquery', methods=['GET', 'POST'])
@cross_origin()
def parse_request():
	option = request.args.get('option')
	subID = urllib.parse.unquote(request.args.get('subject'))
	objID = urllib.parse.unquote(request.args.get('object'))
	predID = request.args.get('predicate')
	print(option, subID, predID, objID)
	response = related_predicate(option, subID, predID, objID)
	return jsonify(response)

@app.route('/')
@cross_origin()
def display_mainpage():
	return render_template('index.html')

if __name__ == '__main__':
	# app.run(debug=True, host='0.0.0.0')
	app.run(debug=True)