import sys

# sys.path.append('/local/home/shrestha/Documents/Thesis/counqer')

import createcsv

if __name__ == '__main__':
	# iteration number to restart from in case of crashes while building the table; default is -1 
	restart = -1
	# table name to store spo triples
	tablename = 'freebase_spot'
	# any specific entity prefixes used by the KB that can be used to detect proper subjects and named entity objects
	kbprefix = ['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.']
	top_predicates = ['http://rdf.freebase.com/ns/common.notable_for.display_name', 
							   'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://rdf.freebase.com/ns/type.object.type',
							   'http://rdf.freebase.com/ns/type.type.instance', 'http://rdf.freebase.com/ns/type.object.key']
	# path to the KB dump file
	infile = './freebase-rdf-latest.gz'
	outfile = './freebase_spot.csv'
	db = createcsv.dbtable(kbprefix, top_predicates)
	createcsv.readttl(infile, outfile, db, restart)
