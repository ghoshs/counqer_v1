import sys

# sys.path.append('/local/home/shrestha/Documents/Thesis/counqer')

import createDB
import db_config as cfg

if __name__ == '__main__':
	# argument to create a new table; if table already exists then no action is taken.
	createtb = True
	# iteratio number to restart from in case of crashes while building the table; default is -1 
	restart = -1
	# table name to store spo triples
	tablename = 'freebase_spot'
	# any specific entity prefixes used by the KB that can be used to detect proper subjects and named entity objects
	kbprefix = ['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.']
	# path to the KB dump file
	filename = '/GW/D5data-11/existential-extraction/freebase-rdf-latest.gz'
	db = createDB.PostgresDB(createtb, tablename, kbprefix, cfg.params)
	createDB.readttl(filename, 'sampleout.ttl', db, restart)
	db.closeconn()
