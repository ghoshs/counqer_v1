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
	fp = open(path + '/' + path.split('/')[-1] + '_' + filename, 'w')
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
			pred_main = label.split('.')[-1]
			domain = label.split('.')[0:-1]
			domain = [' '.join(x.split('_')) for x in domain]
			label = ' '.join(pred_main.split('_')) + ' (' + ', '.join(domain[-2:]) + ')'
			# return ' '.join([x for x in re.split('[^a-zA-Z0-9]', label) if len(x) > 0])
			return label
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

def get_spo(db, predicate, kb_name, limit, obj_type, prev_spo_list=[]):
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	sparql.setReturnFormat(JSON)
	spo_list = []
	if len(prev_spo_list) == 0:
		p_label = get_label(predicate, kb_name, sparql)
	
	cur = db.conn.cursor()
	query = "SELECT * from (SELECT distinct(sub), obj from " + kb_name + " where pred=(%s) and obj_type='" + obj_type +"') as t order by random()"
	cur.execute(query, [predicate])
	row = cur.fetchone()
	count = 0
	while row is not None:
		if count >= limit:
			# fetch all remaining rows
			cur.fetchall()
			break
		s_label = get_label(row[0], kb_name, sparql)
		# do not use triples without labels
		if len(s_label) == 0:
			row = cur.fetchone()
			continue
		# Do not include triples already present in previous batch
		try:
			index1 = prev_spo_list.index(row[0])
			index2 = prev_spo_list.index(row[1])
		except:
			if obj_type is 'int':
				obj = abs(int(row[1])) 
				spo_list.extend([row[0], s_label, obj]) 
				count += 1
			else:
				o_label = get_label(row[1], kb_name, sparql)
				if len(o_label) > 0:
					spo_list.extend([row[0], s_label, o_label])
					count += 1
		row = cur.fetchone()

	if len(prev_spo_list) == 0:
		spo_list.append(p_label)
	else:
		spo_list.extend(prev_spo_list)
	# print('count', count)
	return spo_list

def write_data_item(path, outfile, databuffer):
	fp = open(path + '/' + path.split('/')[-1] + '_' + outfile, 'a')
	writer = csv.writer(fp, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	for item in databuffer:
		item = [x.encode('utf8')  if type(x) not in [str, int, float] else x for x in item]
		writer.writerow(item)
	fp.close()

def populate_fb_labels():
	global fb_label
	file = '/GW/D5data-11/existential-extraction/fb_entity_labels_short.csv'
	with open(file)as fp:
		reader = csv.reader(fp)
		for row in tqdm(reader):
			# only keep English/ digit labels
			if type(row[1]) is bytes:
				try:
					row[1].decode('ascii')
				except Exception as e:
					pass
				else:
					fb_label[row[0]] = row[1].decode('ascii')
		print('Total labels: ', len(fb_label))
		# print('labels',fb_label['m.087d6'])

def read_samples(path, infiles, outfile, oldcols, query_limit=5, obj_type='int'):
	db = DBconn()
	global fb_label
	for infile in infiles:
		kb_name = db.kb_map[infile.split('.csv')[0]]
		if kb_name is 'freebase_spot' and len(fb_label) == 0:
			populate_fb_labels()
		with open(path + '/' + infile) as fp:
			reader = csv.DictReader(fp)
			databuffer = []
			bufferlen = 100
			for row in tqdm(reader):
				data_item = [row[col] for col in oldcols]
				predicate = row[oldcols[0]]
				spo_list = []
				completed = 0
				# spo_list = get_spo(db, predicate, kb_name, query_limit)
				# repeat query till you have 5 english data samples
				while completed < query_limit:
					spo_list = get_spo(db, predicate, kb_name, query_limit - completed, obj_type, spo_list)
					if int((len(spo_list) - 1)/3) == completed:
						break
					completed = int((len(spo_list) - 1)/3)
				# print(completed)

				data_item.extend(spo_list)
				databuffer.append(data_item)
				if len(databuffer) % bufferlen == 0:
					write_data_item(path, outfile, databuffer)
					databuffer = []
			if len(databuffer) > 0:
				write_data_item(path, outfile, databuffer)
	db.closeConn()

def main():
	
	infiles = ['dbp_map.csv', 'dbp_raw.csv', 'wd.csv', 'fb.csv']
	outfile = 'sample.csv'
	query_limit = 5
	newcols = []
	for i in range(0,query_limit):
		newcols.extend(['s'+str(i+1), 's'+str(i+1)+'_label', 'o'+str(i+1)])
	newcols.append('p_label')

	################ Counting Predicates
	# oldcols = ['predicate', 'numeric_10_ptile', 'numeric_90_ptile']
	# path = './test'# test script using the small data in the ./test path
	# create_outfile(path, outfile, oldcols, newcols)
	# read_samples(path, infiles, outfile, oldcols, query_limit, 'int')
	
	# path = './counting'
	# create_outfile(path, outfile, oldcols, newcols)
	# read_samples(path, infiles, outfile, oldcols, query_limit, 'int')

	################ Enumerating Predicates
	oldcols = ['predicate', 'persub_10_ptile_ne', 'persub_90_ptile_ne']
	# path = './test'# test script using the small data in the ./test path
	# create_outfile(path, outfile, oldcols, newcols)
	# read_samples(path, infiles, outfile, oldcols, query_limit, 'named_entity')

	path = './enumerating'
	create_outfile(path, outfile, oldcols, newcols)
	read_samples(path, infiles, outfile, oldcols, query_limit, 'named_entity')

if __name__ == '__main__':
	main()