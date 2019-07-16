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
	# path to the KB dump file
	infile = '/GW/D5data-11/existential-extraction/freebase-rdf-latest.gz'
	outfile = '/GW/D5data-11/existential-extraction/freebase_spot.csv'
	db = createcsv.dbtable(kbprefix)
	createcsv.readttl(infile, outfile, db, restart)
