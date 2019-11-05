from flask import Flask, render_template, url_for, json, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from get_count_data import related_predicate
from text_search import search_wikipedia
try: 
	import urllib2 as myurllib
except ImportError:
	import urllib.request as myurllib

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/ftresults', methods=['GET', 'POST'])
@cross_origin()
def free_text_search():
	print("Query:: ", request.args.get('query'))
	response = search_wikipedia(request.args.get('query'))
	return jsonify(response)

@app.route('/getalignments', methods=['GET','POST'])
@cross_origin()
def get_alignments():
	print(request.args.get('kbname'))
	filename = request.args.get('kbname')+".csv"
	try:
		return send_from_directory('static/data/alignments', filename=filename, as_attachment=True, cache_timeout=0)
	except FileNotFoundError:
		abort(404)

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
