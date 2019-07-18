import csv
from tqdm import tqdm
import postgres_config as cfg
import psycopg2
from psycopg2 import sql
import re
from SPARQLWrapper import SPARQLWrapper, JSON

fb_label = {}

class DBconn():
	def __init__(self):
		self.params = cfg.postgres_params
		self.createConn()
		self.kb_map = {'dbp_map': 'dbpedia_spot', 'dbp_raw': 'dbpedia_spot', 
					   'fb': 'freebase_spot', 'wd': 'wikidata_spot'}

	def createConn(self):
		try:
			self.conn = psycopg2.connect("dbname="+self.params['dbname']+" user="+self.params['user']+" host="+self.params['host']+" password="+self.params['password'])
			print("Connected to the db")
		except:
			print("Unable to connect to the db")

	def closeConn(self):
		if self.conn is not None:
			self.conn.close()
			print("Connection to db closed")

def create_outfile(path, filename, oldcols, newcols):
	fp = open(path + '/' + filename, 'w')
	writer = csv.writer(fp, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(oldcols + newcols)
	fp.close()

def get_label_dbpedia(entity):
	if entity.startswith('http://dbpedia.org/'):
		if '/resource/' in entity:
			return ' '.join(entity.split('/resource/')[-1].split('_'))
		else:
			if '/property/' in entity:
				label = entity.split('/property/')[-1][0].upper() + entity.split('/property/')[-1][1:]
			elif '/ontology/' in entity:
				label = entity.split('/ontology/')[-1][0].upper() + entity.split('/ontology/')[-1][1:]
			else:
				return ''
			if len(re.findall('[A-Z][^A-Z]*', label)) > 0:
				label = ' '.join(re.findall('[A-Z][^A-Z]*', label))
			return label.lower()
	else:
		return ''

def get_label_freebase(entity):
	global fb_label
	if entity.startswith('http://rdf.freebase.com/'):
		if entity.startswith(tuple(['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.'])):
			id = entity.split('http://rdf.freebase.com/ns/')[-1]
			if id in fb_label:
				return fb_label[id]
		else:
			label = entity.split('/')[-1]
			return ' '.join([x for x in re.split('[^a-zA-Z0-9]', label) if len(x) > 0])
	return ''

def get_label_wikidata(entity, sparql):
	if entity.startswith('http://www.wikidata.org/entity/'):
		query = ("SELECT * WHERE { <" + entity + "> rdfs:label ?label ."
				 "FILTER (langMatches(lang(?label), 'EN'))"
				 "} limit 1"
				 )
		sparql.setQuery(query)
		results = sparql.query().convert()
		if 'results' in results:
			for item in results["results"]["bindings"]:
				return item["label"]["value"]
	elif entity.startswith('http://www.wikidata.org/prop/'):
		query = ("SELECT * WHERE { <http://www.wikidata.org/entity/" + entity.split('/')[-1] + "> rdfs:label ?label ."
				 "FILTER (langMatches(lang(?label), 'EN'))"
				 "} limit 1"
				 )
		sparql.setQuery(query)
		results = sparql.query().convert()
		if 'results' in results:
			for item in results["results"]["bindings"]:
				return item["label"]["value"]

	return ''

def get_label(entity, kb_name, sparql):
	if kb_name == 'dbpedia_spot':
		return get_label_dbpedia(entity)
	elif kb_name == 'freebase_spot':
		return get_label_freebase(entity)
	elif kb_name == 'wikidata_spot':
		return get_label_wikidata(entity, sparql)
	else:
		return ''

def get_spo(db, predicate, kb_name, limit):
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	sparql.setReturnFormat(JSON)
	spo_list = []
	cur = db.conn.cursor()
	query = "SELECT * from (SELECT distinct(sub), obj from " + kb_name + " where pred=(%s) and obj_type='int') as t order by random() limit " + str(limit)
	cur.execute(query, [predicate])
	# predicate may have only one triple
	row = cur.fetchone()
	while row is not None:
		s_label = get_label(row[0], kb_name, sparql)
		o_label = get_label(row[1], kb_name, sparql)
		spo_list.extend([row[0], s_label, row[1], o_label])
		row = cur.fetchone()
	p_label = get_label(predicate, kb_name, sparql)
	if len(spo_list) < limit*4:
		l = len(spo_list)
		spo_list.extend(['' for i in range(0,limit*4-l)])
	spo_list.append(p_label)
	return spo_list

def write_data_item(path, outfile, databuffer):
	fp = open(path + '/' + outfile, 'a')
	writer = csv.writer(fp, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	for item in databuffer:
		writer.writerow(item)
	fp.close()

def populate_fb_labels():
	global fb_label
	file = '/GW/D5data-11/existential-extraction/fb_entity_labels_short.csv'
	with open(file)as fp:
		reader = csv.reader(fp)
		for row in tqdm(reader):
			fb_label[row[0]] = row[1]
		print('labels',fb_label['m.087d6'])

def read_samples(path, infiles, outfile, oldcols):
	db = DBconn()
	query_limit = 2
	for infile in infiles:
		kb_name = db.kb_map[infile.split('.csv')[0]]
		if kb_name is 'freebase_spot':
			populate_fb_labels()
		with open(path + '/' + infile) as fp:
			reader = csv.DictReader(fp)
			databuffer = []
			bufferlen = 100
			for row in tqdm(reader):
				data_item = [row[col] for col in oldcols]
				predicate = row[oldcols[0]]
				spo_list = get_spo(db, predicate, kb_name, query_limit)
				data_item.extend(spo_list)
				databuffer.append(data_item)
				if len(databuffer) % bufferlen == 0:
					write_data_item(path, outfile, databuffer)
					databuffer = []
			if len(databuffer) > 0:
				write_data_item(path, outfile, databuffer)
	db.closeConn()

def main():
	# test script using the small data in the ./test path
	path = './counting'
	infiles = ['dbp_map.csv', 'dbp_raw.csv', 'wd.csv', 'fb.csv']
	outfile = 'sample.csv'
	oldcols = ['predicate', 'numeric_10_ptile', 'numeric_90_ptile']
	newcols = ['s1', 's1_label', 'o1', 'o1_label', 's2', 's2_label', 'o2', 'o2_label', 'p_label']

	create_outfile(path, outfile, oldcols, newcols)
	read_samples(path, infiles, outfile, oldcols)
	# infiles = ['fb.csv']
	# read_samples(path, infiles, outfile, oldcols)

if __name__ == '__main__':
	main()