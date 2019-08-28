import csv

def shorten_kb_entities(kb_name, prefix):
	filename=kb_name+'_entities.csv'
	fileout=kb_name+'_entities_short.csv'

	fout = open(fileout, 'w')
	writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
	with open(filename) as fp:
		reader = csv.reader(fp)
		for row in reader:
			if prefix in row[0]:
				writer.writerow([row[0].split(prefix)[-1]])
			else:
				writer.writerow(row)
	fout.close()

def main():
	shorten_kb_entities('dbpedia', 'http://dbpedia.org/resource/')
	shorten_kb_entities('wikidata', 'http://www.wikidata.org/entity/')

if __name__ == '__main__':
	main()