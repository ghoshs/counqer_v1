# from psycopg2 import sql
# import db_config as cfg

import re
import gzip
import csv
from tqdm import tqdm
from rdflib import Graph
import multiprocessing as mp
from joblib import Parallel, delayed

class dbtable():
	def __init__(self, kbprefix):
		self.prefix = kbprefix
		self.top5_predicate = ['http://rdf.freebase.com/ns/common.notable_for.display_name', 
							   'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://rdf.freebase.com/ns/type.object.type',
							   'http://rdf.freebase.com/ns/type.type.instance', 'http://rdf.freebase.com/ns/type.object.key']

		self.readbuffer = 20000
		self.writebuffer = 50
		# self.triple_count = mp.Value('i', 0)

def find_type(pred, val, db):
	valtype=None
	measure = ['latm', 'lats', 'latdeg', 'longm', 'longs', 'longdeg', 'score', 'height', 'weight', 'length', 'width', 'high', 'low', 'speed', 
				'rank', 'coordinate', 'kgs', 'long', 'date', 'year', 'month', 'time', 'abbreviation', 'address', 'code',
				'1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '#', '_']
	# date = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
	date = re.compile(r'^(1|2)[0-9]{3}(-[0-9]{2})?(-[0-9]{2})?$')
	# check integer type
	try:
		tmp = int(val)
	except ValueError:
		pass
	else: 
		valtype = 'int'

	# check float type
	if valtype is None: 
		try:
			tmp = float(val)
		except ValueError:
			pass
		else:
			valtype = 'float'
	
	#check date type
	probable_date = True if (valtype == 'int' and 'numberOf' not in pred and len(val) == 4 and int(val) >= 1400 and int(val) <= 2050) else False
	if valtype is None or probable_date:
		# filter only those 4 digit int which are not potential count candidates 
		valtype = 'date' if re.match(date, val) is not None else None

	# check entitty type
	if valtype is None and val.startswith(tuple(db.prefix)):
		valtype = 'named_entity'

	if valtype is None:
		valtype = 'unknown'

	return valtype

def write_file(outfile, writelist, db, iter, j):
	csvfile = open(outfile, 'a')
	writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)
	for item in writelist:
		try:
			writer.writerow([item[0], item[1], item[2], item[3]])
		except Exception as e:
			print('write file exp at iter:%d  (s,p,o,type) = (%s)' %((iter - db.readbuffer + j*db.writebuffer + k), ','.join(item)))
	csvfile.close()

def insertValues(ttllist, db, outfile, iter, j):
	writelist = []
	for line in ttllist:
		g = Graph()	
		g.parse(data=line, format='turtle')
		for s,p,o in g:
			if not s.startswith(tuple(db.prefix)):
				continue
			if any(val in p for val in db.top5_predicate):
				continue
			valtype=find_type(p, o, db)
			writelist.append([s.encode('utf-8'), p.encode('utf-8'), o.encode('utf-8'), valtype])
	try:
		write_file(outfile, writelist, db, iter, j)
	except Exception as e:
		print('write exp; ',e)
		# else:
			# db.triple_count.value += 1

def readttl(infile, outfile, db, restart=0):
	if restart == 0:
		csvfile = open(outfile, 'w')
		writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)
		writer.writerow(['sub', 'pred', 'obj', 'obj_type'])
		csvfile.close()

	cores = mp.cpu_count()
	# pool = mp.Pool(cores)
	# jobs = []

	with gzip.open(infile, 'rt') as fp:
		ttlcontent = []
		counter = 0
		for i, line in tqdm(enumerate(fp)):
			if i <= restart:
				continue
			else:
				if counter < db.readbuffer:
					ttlcontent.append(line)
					counter += 1
				else:
					try:
						Parallel(n_jobs = cores)(delayed(insertValues)(ttlcontent[j: j+db.writebuffer if (j+db.writebuffer) <= len(ttlcontent) else len(ttlcontent)], 
							db, outfile, i, j) for j in range(0, len(ttlcontent), db.writebuffer))
						# insertValues(ttlcontent, db, outfile, i)
					except Exception as e:
						print('insert exp: ',e)
						# print('%d line not inserted %s'%(i, line))
					else:
						counter = 0
						ttlcontent = []
						# triple_count = triple_count + 1
		if len(ttlcontent) > 0:
			try:
				Parallel(n_jobs = cores)(delayed(insertValues)(ttlcontent[j: j+db.writebuffer if (j+db.writebuffer) <= len(ttlcontent) else len(ttlcontent)], 
							db, outfile, i, j) for j in range(0, len(ttlcontent), db.writebuffer))
				# insertValues(ttlcontent, db, outfile, i)
			except Exception as e:
				print('insert exp: ',e)
	# print("Triples committed in %s = %d\n" %(infile, db.triple_count.value))


def main():
	kbprefix = ['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.']
	db = dbtable(kbprefix)
	restart = 0
	infile = '/GW/D5data-11/existential-extraction/freebase-rdf-latest.gz'
	outfile = '/GW/D5data-11/existential-extraction/freebase_spot_1.csv'
	# infile = 'sampleout.ttl.gz'
	# outfile = 'sampleout.csv'
	readttl(infile, outfile, db, restart)

if __name__ == '__main__':
	main()