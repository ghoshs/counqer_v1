import psycopg2
from psycopg2 import sql
from rdflib import Graph
import os
from collections import namedtuple
import re
from tqdm import tqdm
import gzip

geo_names = set([])
ppl_names = set([])

class PostgresDB:

	def __init__(self, createtb, tablename, kbprefix, params):
		self.createDBconn(params)
		if createtb:
			self.createTable(tablename)
		else:
			print('Skipping Creating Table!!')

		self.tablename = tablename
		self.prefix = kbprefix
		# self.SPO = namedtuple('SPO', 'sub pred obj')

	def createDBconn(self, params):
		try: 
			self.conn = psycopg2.connect("dbname="+params['dbname']+" user="+params['user']+" host="+params['host']+" password="+params['password'])
			print "Connected to the db"
		except:
			print "Unable to connect to the db"

	def createTable(self, tablename):
		cur = self.conn.cursor()
		cur.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {}
             (sub text, pred text, obj text, obj_type text)
				""").format(sql.Identifier(tablename)))
		self.conn.commit()
		print "Table created if does not exist"
		cur.close()

	def closeconn(self):
		if self.conn is not None:
			self.conn.close()
			print "Connection to db closed"


def get_names(fname):
	fname = open(fname, 'r').read()
	names = fname.split('\n')
	names = [x for x in names if len(x)>2]
	names = [' '+x.lower()+' ' for x in names]
	return set(names)

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

	# check people or city names in string values
	# pred_name = pred.lower()
	# if valtype is None and not any(m in pred_name for m in measure) and not (val.isupper() or ',' in val):
	# 	# print(type(val), val)
	# 	num_words = len(re.findall(r'\w+', val))
	# 	num_cap_words = len(re.findall('([A-Z])\w+', val))

	# 	if num_cap_words > 1 or num_words < 5:
	# 		val = ' '+val.lower()+' '
	# 		if any(name in val for name in ppl_names):
	# 			valtype = 'name_person'
	# 		elif any(name in val for name in geo_names):
	# 			valtype = 'name_city'

	if valtype is None:
		valtype = 'unknown'

	return valtype

def insertValues(outfile, db, iter):
	g = Graph()
	cur = db.conn.cursor()
	# gdict = {}
	g.parse(outfile, format='turtle')
	i= 1
	for s,p,o in g:
		# print s.encode('utf-8'),p.encode('utf-8'),o.encode('utf-8')
		if not s.encode('utf-8').startswith(tuple(db.prefix)):
			# do not insert tuples whose subject is a property
			continue
		valtype=find_type(p.encode('utf-8'), o.encode('utf-8'), db)
		try:
			cur.execute(sql.SQL("""INSERT INTO {}(sub, pred, obj, obj_type) VALUES (%s, %s, %s, %s)""").format(sql.Identifier(db.tablename)), (s, p, o, valtype,))
		except:
			print("s: %s; p: %s; o: %s" %(s,p,o))
			print('Stopped at triple count: %d\n' %(iter-10000+i))
		finally:
			i += 1
	db.conn.commit()
	cur.close()

def readttl(infile, outfile, db, restart):
	with gzip.open(infile, 'rt') as fp:
		ttlcontent = [] 
		counter = 0
		triple_count = 0
		for i, line in tqdm(enumerate(fp)):
			if i < restart:
				continue
			# elif i>=(restart-5) and i <= restart+1:
				# print(line)
			else:
				# break
				ttlcontent.append(line)
				counter = counter + 1
				triple_count = triple_count + 1
				# out.write(line+'\n')
				if counter < 10000:
					continue
					# line = fp.readline()  
				else:
					out = open(outfile, 'w')
					out.write('\n'.join(ttlcontent))
					out.close()
					insertValues(outfile, db, i)
					# if triple_count%10000 == 0:
						# print("Triples committed = %d\n" %(triple_count))
					os.remove(outfile)
					counter = 0
					ttlcontent = []

	if len(ttlcontent)>0:		
		out = open(outfile, 'w')
		out.write('\n'.join(ttlcontent))
		out.close()
		# try:
		insertValues(outfile, db, i)
		# except:	
		os.remove(outfile)
	print("Triples committed in %s = %d\n" %(infile, triple_count))

	# fp.close()
	# out.close()

# def querydb(db):
# 	commands = ["""SELECT pred, COUNT (pred) from triples GROUP BY pred ORDER BY count DESC;""", 
# 	"""SELECT COUNT(pred) FROM triples""",
# 	"""select pred, t.count from (select pred, count (pred) from spotriples group by pred order by count desc) as t where t.count > 10000;""",
# 	"""select count(*) from (select pred, count (pred) from spotriples group by pred order by count desc) as t where t.count > 10000;"""]
# 	cur = db.conn.cursor()
# 	cur.execute(commands[1])
# 	print("The number of parts: ", cur.rowcount)
# 	row = cur.fetchone()
# 	print(row)
# 	## For multiline result 
# 	# while row is not None:
# 	# 	print(row)
# 	# 	row = cur.fetchone()
# 	cur.close()


if __name__ == '__main__':
	createtb=True
	tablename = 'spot_triples'
	db = PostgresDB(createtb, tablename, 'http://dbpedia.org/')
	# global ppl_names, geo_names
	# restart = 4762899
	restart = 0
	# ppl_names = get_names('entity_names/firstnames.txt')
	# geo_names = get_names('entity_names/citynames.txt')
	# readttl('../../DBdump/infobox_properties_en.ttl')
	# readttl('/GW/D5data-8/existential-extraction/dbpedia/infobox_properties_en.ttl', 'sampleout.ttl',db, restart)
	# readttl('/GW/D5data-9/existential-extraction/dbpedia/mappingbased_literals_en.ttl', 'sampleout.ttl', db, restart)
	# readttl('/GW/D5data-9/existential-extraction/dbpedia/mappingbased_objects_en.ttl', 'sampleout.ttl', db, restart)
	# querydb(db)
	db.closeconn()