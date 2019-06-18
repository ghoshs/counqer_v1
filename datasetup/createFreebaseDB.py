import sys

# sys.path.append('/local/home/shrestha/Documents/Thesis/counqer')

import createDB
import db_config as cfg

if __name__ == '__main__':
	createtb = True
	restart = 40780000
	tablename = 'freebase_spot'
	kbprefix = 'http://rdf.freebase.com/'
	filename = '/GW/D5data-11/existential-extraction/freebase-rdf-latest.gz'
	db = createDB.PostgresDB(createtb, tablename, kbprefix, cfg.params)
	createDB.readttl(filename, 'sampleout.ttl', db, restart)
	db.closeconn()
