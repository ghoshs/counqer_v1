from pyhive.hive import *
from thrift.transport.TTransport import *
import db_config as cfg

class Hive:
	def __init__(self):
		self.get_connection()
	def get_connection(self):
		self.conn = connect(cfg.hive_params['host'], username=cfg.hive_params['user'])
	def close_connection(self):
		self.conn.close()


# function to create a table from a csv file stored in the HDFS
def create_table(pyhv):
	cur = pyhv.conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS ghoshs_sample (sub string, pred string, obj string) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION '/user/ghoshs/FB' TBLPROPERTIES ('skip.header.line.count' = '1')")
	# pyhv.conn.commit()
	cur.close()

# function to drop a table if it exists
def drop_table(pyhv):
	cur = pyhv.conn.cursor()
	cur.execute("DROP TABLE IF EXISTS ghoshs_sample")
	cur.close()

# function to display all tables in the Hive metastore
def show_table(pyhv):
	cur = pyhv.conn.cursor()
	cur.execute('SHOW TABLES')
	for row in cur.fetchall():
		print(row)
	cur.close()

# function to fetch samples from a table
def show_samples(pyhv):
	cur = pyhv.conn.cursor()
	cur.execute('SELECT * from ghoshs_sample')
	for row in cur.fetchall():
		print(row)
	cur.close()

def main():
	pyhv = Hive()
	create_table(pyhv)
	show_table(pyhv)
	pyhv.close_connection()

if __name__ == '__main__':
	main()