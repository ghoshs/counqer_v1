import csv
from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON

def write_to_file(filein, fileout, sparql, resume=0):

	with open(filein, 'r') as fp:
		reader = csv.reader(fp)
		# skip header
		next(reader, None)
		rownum = 1
		for row in tqdm(reader):
			if rownum < resume:
				rownum += 1
				continue
			sameAs = {}
			sparql.setQuery('SELECT ?o WHERE {<http://dbpedia.org/resource/' + row[0] + '> owl:sameAs ?o.}')
			results = sparql.query().convert()
			for value in results["results"]["bindings"]:
				if value["o"]["type"] == "uri":
					if 'http://rdf.freebase.com/ns/' in value["o"]["value"] and 'fb' not in sameAs:
						sameAs['fb'] = value["o"]["value"].split('http://rdf.freebase.com/ns/')[-1]
					elif 'http://www.wikidata.org/entity/' in value["o"]["value"] and 'wd' not in sameAs:
						sameAs['wd'] = value["o"]["value"].split('http://www.wikidata.org/entity/')[-1]
			if 'wd' not in sameAs:
				sameAs['wd'] = '-'
			if 'fb' not in sameAs:
				sameAs['fb'] = '-'
			with open(fileout, 'a') as fout:
				writer = csv.writer(fout, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
				writer.writerow([row[0], sameAs['wd'], sameAs['fb']])
def main():
	filein = 'dbpedia_entities_short.csv'
	fileout = 'entity_map_sameAs_dbp.csv'

	dbp_sparql = SPARQLWrapper("http://dbpedia.org/sparql")
	dbp_sparql.setReturnFormat(JSON)

	resume = 213153

	if resume == 0:
		fpout = open(fileout, 'w') 
		writer = csv.writer(fpout, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['dbpedia', 'wikidata', 'freebase'])
		fpout.close()
	
	write_to_file(filein, fileout, dbp_sparql, resume)

if __name__ == '__main__':
	main()