import psycopg2
from psycopg2 import sql
import numpy as np
import csv
from tqdm import tqdm
import unicodedata
import re

class PostgresDB:

	def __init__(self, tablename, params):
		self.tablename = tablename['property']
		self.spot_tb = tablename['spot']
		self.csvpath = ''
		self.createDBconn(params)
		# if createtb:
		# 	self.create_pred_property_Table(tablename['direct'])
		# 	self.create_invpred_property_Table(tablename['inverse'])
		# else:
		# 	print('Skipping Creating Tables!!')

	def createDBconn(self, params):
		try: 
			self.conn = psycopg2.connect("dbname="+params['dbname']+" user="+params['user']+" host="+params['host']+" password="+params['password'])
			print "Connected to the db"
		except:
			print "Unable to connect to the db"

	def create_pred_property_Table(self):
		cur = self.conn.cursor()
		# 'Frequency', 'Percent_dist_comma_sep',
		# 'Percent_dist_int', 'Percent_dist_float', 'Percent_dist_date', 'Percent_dist_named_entity', 'Percent_dist_unknown',
		# 'Numeric_dist_max', 'Numeric_dist_min', 'Numeric_dist_avg', 'Numeric_dist_10_percentile', 'Numeric_dist_90_percentile',
		#  Value_max_NE, Value_min_NE, Value_avg_NE, Value_10_ptile_NE, Value_90_ptile_NE,

		cur.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {}
					(
						Predicate text, 
						Frequency bigint, 
						Pcent_comma_sep numeric, Pcent_int numeric, Pcent_float numeric, Pcent_date numeric, Pcent_NE numeric, Pcent_unk numeric, 
						Numeric_max numeric, Numeric_min numeric, Numeric_avg numeric, 
						Numeric_10_ptile numeric, Numeric_90_ptile numeric, 
						PerSub_max_NE numeric, PerSub_min_NE numeric, PerSub_avg_NE numeric,
						PerSub_10_ptile_NE numeric, PerSub_90_ptile_NE numeric,
						PerSub_max_int numeric, PerSub_min_int numeric, PerSub_avg_int numeric,
						PerSub_10_ptile_int numeric, PerSub_90_ptile_int numeric,
						PRIMARY KEY (Predicate)	
					) 
					""").format(sql.Identifier(self.tablename)))
		self.conn.commit()
		print "Property Table created if does not exist!!\n"
		cur.close()		

	def create_invpred_property_Table(self):
		cur = self.conn.cursor()

		cur.execute(sql.SQL("""CREATE TABLE IF NOT EXISTS {}
					(
						Pred_inv text, Frequency bigint,
						PerSub_max_NE numeric, PerSub_min_NE numeric, PerSub_avg_NE numeric,
						PerSub_10_ptile_NE numeric, PerSub_90_ptile_NE numeric,
						PRIMARY KEY (Pred_inv)	
					) 
					""").format(sql.Identifier(self.tablename)))
		self.conn.commit()
		print "Inverse Property Table created if does not exist!!\n"
		cur.close()		

	def closeconn(self):
		if self.conn is not None:
			self.conn.close()
			print "Connection to db closed"

def get_type_count(pred, db):
	cur = db.conn.cursor()
	types={}
	query = "SELECT obj_type, count(*) FROM " + db.spot_tb + " where pred=(%s) group by obj_type"
	cur.execute(query, [pred])
	row = cur.fetchone()
	while row is not None:
		types[row[0]] = row[1]
		row = cur.fetchone()
	cur.close()
	return types

def get_persub_val(pred, db):
	cur = db.conn.cursor()
	types = {}
	count_list = []
	query = "select count(*) from " + db.spot_tb + " where pred=(%s) and obj_type='int' group by sub"
	cur.execute(query, [pred])
	for row in cur:
		count_list.append(row[0])
	cur.close()
	types['max'] = max(count_list)
	types['min'] = min(count_list)
	types['avg'] = sum(count_list)/float(len(count_list))
	np.asarray(count_list)
	types['p10'] = np.percentile(count_list, 10)
	types['p90'] = np.percentile(count_list, 90)
	return types

def get_type_numeric(pred, db):
	cur = db.conn.cursor()
	types = {}
	obj_list = []
	# cur.execute("""select max(a.obj1), min(a.obj1), avg(a.obj1), percentile_disc(0.1) within group (order by a.obj1) as p10, 
	# 	percentile_disc(0.9) within group (order by a.obj1) as p90 
	# 	from (select cast(obj as bigint) as obj1 
	# 	from spot_triples where pred=(%s) and obj_type='int') a""", [pred])
	query = "select obj from " + db.spot_tb + " where pred=(%s) and obj_type='int' "
	cur.execute(query, [pred])
	for row in cur:
		val = 0
		try: 
			val = int(row[0])
		except ValueError:
			# print (pred, row)
			try:
				unicode_char_list = ''.join([str(unicodedata.decimal(d, -1)) for d in row[0].decode('utf8')])
				val = int(unicode_char_list)
			except Exception as e:
				print(pred, row[0], e)
		else:
			obj_list.append(abs(val))
	cur.close()
	types['max'] = max(obj_list)
	types['min'] = min(obj_list)
	types['avg'] = sum(obj_list)/float(len(obj_list))
	np.asarray(obj_list)
	types['p10'] = np.percentile(obj_list, 10)
	types['p90'] = np.percentile(obj_list, 90)
	return types

def get_type_value(pred, db):
	cur = db.conn.cursor()
	types = {}
	count_list = []
	# cur.execute("""select max(a.cnt1), min(a.cnt1), avg(a.cnt1) 
	# 	from (select sub, count(*) as cnt1 from spot_triples 
	# 	where pred=(%s) and obj_type='named_entity' group by sub) as a""", [pred])
	query = "select count(*) from " + db.spot_tb + " where pred=(%s) and obj_type='named_entity' group by sub"
	cur.execute(query, [pred])
	for row in cur:
		count_list.append(row[0])
	cur.close()
	types['max'] = max(count_list)
	types['min'] = min(count_list)
	types['avg'] = sum(count_list)/float(len(count_list))
	np.asarray(count_list)
	types['p10'] = np.percentile(count_list, 10)
	types['p90'] = np.percentile(count_list, 90)
	return types

def get_type_comma_sep(pred, db):
	cur = db.conn.cursor()
	freq = 0
	list_str = re.compile(r'(\s*,\s*[^\s]+)+')
	query = "select obj from " + db.spot_tb + " where pred=(%s) and obj_type='unknown'"
	cur.execute(query, [pred]) 
		# and obj similar to '\w+(\s*,\s*\w+)*'""", [pred])
	row = cur.fetchone()
	while row is not None:
		obj = row[0]
		if re.match(list_str, obj) is not None:
			freq += 1
		row = cur.fetchone()
	cur.close()
	return freq

def update_prop_table(db, pred, freq, percent_dist_dict, numeric_dist_dict, value_dist_dict, dist_comma_sep, persub_val_int):
	cur = db.conn.cursor()
	query = ("INSERT INTO " + db.tablename + "(Predicate, Frequency, "
				"Pcent_comma_sep, Pcent_int, Pcent_float, Pcent_date, Pcent_NE, Pcent_unk, "
				"Numeric_max, Numeric_min, Numeric_avg, "
				"Numeric_10_ptile, Numeric_90_ptile, "
				"PerSub_max_NE, PerSub_min_NE, PerSub_avg_NE, "
				"PerSub_10_ptile_NE, PerSub_90_ptile_NE, "
				"PerSub_max_int, PerSub_min_int, PerSub_avg_int, "
				"PerSub_10_ptile_int, PerSub_90_ptile_int) "
				"VALUES "
				"(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
	cur.execute(query, 
				(pred, freq, dist_comma_sep, 
					percent_dist_dict['int'], percent_dist_dict['float'], percent_dist_dict['date'], 
					percent_dist_dict['named_entity'], percent_dist_dict['unknown'],
					numeric_dist_dict['max'], numeric_dist_dict['min'], numeric_dist_dict['avg'],
					numeric_dist_dict['p10'], numeric_dist_dict['p90'],
					value_dist_dict['max'], value_dist_dict['min'], value_dist_dict['avg'],
					value_dist_dict['p10'], value_dist_dict['p90'],
					persub_val_int['max'], persub_val_int['min'], persub_val_int['avg'],
					persub_val_int['p10'], persub_val_int['p90']))
	db.conn.commit()
	cur.close()

def create_direct_csv_file(db):
	path = db.csvpath + db.tablename + '.csv'
	csvfile = open(path, 'w')
	writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['Predicate', 'Frequency', 
				'Pcent_comma_sep', 'Pcent_int', 'Pcent_float', 'Pcent_date', 'Pcent_NE', 'Pcent_unk', 
				'Numeric_max', 'Numeric_min', 'Numeric_avg', 
				'Numeric_10_ptile', 'Numeric_90_ptile', 
				'PerSub_max_NE', 'PerSub_min_NE', 'PerSub_avg_NE',
				'PerSub_10_ptile_NE', 'PerSub_90_ptile_NE',
				'PerSub_max_int', 'PerSub_min_int', 'PerSub_avg_int',
				'PerSub_10_ptile_int', 'PerSub_90_ptile_int'])
	csvfile.close()

def write_to_csv(db, pred, freq, percent_dist_dict, numeric_dist_dict, value_dist_dict, dist_comma_sep, persub_val_int):
	path = db.csvpath + db.tablename + '.csv'
	csvfile = open(path, 'a')
	writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	writer.writerow([pred, freq, dist_comma_sep, 
					percent_dist_dict['int'], percent_dist_dict['float'], percent_dist_dict['date'], 
					percent_dist_dict['named_entity'], percent_dist_dict['unknown'],
					numeric_dist_dict['max'], numeric_dist_dict['min'], numeric_dist_dict['avg'],
					numeric_dist_dict['p10'], numeric_dist_dict['p90'],
					value_dist_dict['max'], value_dist_dict['min'], value_dist_dict['avg'],
					value_dist_dict['p10'], value_dist_dict['p90'],
					persub_val_int['max'], persub_val_int['min'], persub_val_int['avg'],
					persub_val_int['p10'], persub_val_int['p90']])
	csvfile.close()

def generate_details(predfreq_filename, db, cutoff):
	# predfreq = open(predfreq_filename, 'r').read().split('\n')
	# predfreq = predfreq[1:-1]
	# print("Length predfreq: ", len(predfreq))
	# cutoff = 1000

	with open(predfreq_filename, 'r') as fp:
		predfreq = csv.reader(fp, delimiter=',', quotechar='"')

		for i, row in tqdm(enumerate(predfreq)):
			if (i==0):
				# bypass header
				continue
			pred = row[0]
			freq = int(row[1])
			# Append to previous KB
			if (cutoff['required'] and freq >= cutoff['value']):
				continue

			# Get frequency distribution of value types taken by the predicate 
			percent_dist_dict = get_type_count(pred, db)
			
			numeric_dist_dict = None
			value_dist_dict = None
			dist_comma_sep = 0
			persub_val_int = None

			if 'int' in percent_dist_dict:
				numeric_dist_dict = get_type_numeric(pred, db)
				persub_val_int = get_persub_val(pred, db)
				percent_dist_dict['int'] = percent_dist_dict['int']/float(freq)
			else:
				percent_dist_dict['int'] = 0.0

			if 'float' in percent_dist_dict:
				percent_dist_dict['float'] = percent_dist_dict['float']/float(freq)
			else:
				percent_dist_dict['float'] = 0.0

			if 'date' in percent_dist_dict:
				percent_dist_dict['date'] = percent_dist_dict['date']/float(freq)
			else:
				percent_dist_dict['date'] = 0.0

			if 'named_entity' in percent_dist_dict:
				value_dist_dict = get_type_value(pred, db)
				percent_dist_dict['named_entity'] = percent_dist_dict['named_entity']/float(freq)
			else:
				percent_dist_dict['named_entity'] = 0.0

			if 'unknown' in percent_dist_dict:
				dist_comma_sep = get_type_comma_sep(pred, db)
				percent_dist_dict['unknown'] = (percent_dist_dict['unknown'] - dist_comma_sep)/float(freq)
			else:
				percent_dist_dict['unknown'] = 0.0
			dist_comma_sep = dist_comma_sep/float(freq)

			if numeric_dist_dict is None:
				numeric_dist_dict = {'max': None, 'min': None, 'avg': None, 'p10': None, 'p90': None}
			if value_dist_dict is None:
				value_dist_dict = {'max': None, 'min': None, 'avg': None, 'p10': None, 'p90': None}
			if persub_val_int is None:
				persub_val_int = {'max': None, 'min': None, 'avg': None, 'p10': None, 'p90': None}

			write_to_csv(db, pred, freq, percent_dist_dict, numeric_dist_dict, value_dist_dict, dist_comma_sep, persub_val_int)

def modify_details(tweak_name, db):
	fp=open('Tweaknames.txt', 'r').read().split('\n')[1:-1]
	print("%d predicates\n"%len(fp))
	for i, pred in enumerate(fp):
		pred = pred[1:-1]
		persub_val_int = None
		persub_val_int = get_persub_val(pred, db)
		cur = db.conn.cursor()
		cur.execute("""UPDATE pred_property
					SET PerSub_max_int=(%s), 
						PerSub_min_int=(%s), 
						PerSub_avg_int=(%s),
						PerSub_10_ptile_int=(%s),
						PerSub_90_ptile_int=(%s) 
					WHERE predicate=(%s) 
					""", 
					(persub_val_int['max'], persub_val_int['min'], persub_val_int['avg'],
						persub_val_int['p10'], persub_val_int['p90'], pred))
		db.conn.commit()
		cur.close()
		# print('breaking!!\n')
		# break
		if ((i+1)%100 == 0):
			print('%d predicates updated!'%(i+1))

def get_inv_type_value(pred, db):
	cur = db.conn.cursor()
	types = {}
	count_list = []
	query = "select count(*) from " + db.spot_tb + " where pred=(%s) and obj_type = 'named_entity' group by obj"
	cur.execute(query, [pred])
	for row in cur:
		count_list.append(row[0])
	cur.close()
	if len(count_list) == 0:
		return None
	# types['freq'] = sum(count_list)
	types['max'] = max(count_list)
	types['min'] = min(count_list)
	types['avg'] = sum(count_list)/float(len(count_list))
	np.asarray(count_list)
	types['p10'] = np.percentile(count_list, 10)
	types['p90'] = np.percentile(count_list, 90)
	return types

def update_invprop_table(db, pred, freq, value_dist_dict):
	cur = db.conn.cursor()
	query = ("INSERT INTO " + db.tablename + "(pred_inv, "
					"PerSub_max_NE, "
					"PerSub_min_NE, "
					"PerSub_avg_NE, "
					"PerSub_10_ptile_NE, "
					"PerSub_90_ptile_NE, "
					"frequency) "
					"VALUES "
					"(%s, %s, %s, %s, %s, %s, %s)")
	cur.execute(query, 
				(pred, 
					value_dist_dict['max'], value_dist_dict['min'], value_dist_dict['avg'],
					value_dist_dict['p10'], value_dist_dict['p90'], freq
				))
	db.conn.commit()
	cur.close()

def create_inverse_csv_file(db):
	path = db.csvpath + db.tablename + '.csv'
	csvfile = open(path, 'w')
	writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['Pred_inv', 'Frequency',
						'PerSub_max_NE', 'PerSub_min_NE', 'PerSub_avg_NE',
						'PerSub_10_ptile_NE', 'PerSub_90_ptile_NE'])
	csvfile.close()

def write_to_invprop_csv(db, pred, freq, value_dist_dict):
	path = db.csvpath + db.tablename + '.csv'
	csvfile = open(path, 'a')
	writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
	writer.writerow([pred, freq, 
					value_dist_dict['max'], value_dist_dict['min'], value_dist_dict['avg'],
					value_dist_dict['p10'], value_dist_dict['p90']])
	csvfile.close()

def generate_inv_pred_details(predfreq_filename, db, cutoff):
	# predfreq = open(predfreq_filename, 'r').read().split('\n')
	# predfreq = predfreq[1:-1]
	# print("Length predfreq: ", len(predfreq))
	# cutoff = 1000
	# db.create_invpred_property_Table()
	with open(predfreq_filename, 'r') as fp:
		predfreq = csv.reader(fp, delimiter=',', quotechar='"')
		for i, item in tqdm(enumerate(predfreq)):
			if i == 0:
				# bypass header
				continue
			pred = item[0]
			freq = int(item[1])

			if (cutoff['required'] and freq >= cutoff['value']):
				continue

			value_dist_dict = None
			value_dist_dict = get_inv_type_value(pred, db)
			
			if value_dist_dict is None:
				# predicate does not exist as inverse
				continue
			write_to_invprop_csv(db, pred, freq, value_dist_dict)
			# if (i%100 == 0):
			# print('%d predicates inserted!'%(i+1)) 


# def main():
# 	predfreq_filename = 'predfreq_p_all.csv'
# 	# tweak_name = 'Tweaknames.txt' # generate per subject details for only frequent predicates
# 	# predtypes_filename = 'predtypes.csv'
# 	createtb=False
# 	db = PostgresDB(createtb)
# 	### create property details
# 	# cutoff = 100
# 	generate_details(predfreq_filename, db)
# 	# modify_details(tweak_name, db)
# 	print('Direct properties complete!!!\n Starting inverse properties\n')
# 	### create inverse property details
# 	# predfreq_filename = 'inv_predfreq_p_all.csv'
# 	resume = True
# 	generate_inv_pred_details(predfreq_filename, db, cutoff)

# 	db.closeconn()

# if __name__ == '__main__':
# 	main()