setwd('/local/home/shrestha/Documents/Thesis/counqer')

counting <- read.csv('alignment/counting_filtered.csv')

set.seed(17)
dbp_map <- as.character(droplevels(sample(counting[grep("http://dbpedia.org/ontology/", counting$x),], size = 75)))
  
set.seed(17)
dbp_raw <- as.character(droplevels(sample(counting[grep("http://dbpedia.org/property/", counting$x),], size = 75)))

set.seed(17)
wd <- as.character(droplevels(sample(counting[grep("http://www.wikidata.org/prop/direct", counting$x),], size = 75)))

set.seed(17)
fb <- as.character(droplevels(sample(counting[grep("http://rdf.freebase.com/", counting$x),], size = 75)))

data <- append(dbp_map, append(dbp_raw, append(wd, fb)))
write.csv(data, 'alignment_crowd_annotations/eval_questions/prednames/counting.csv', row.names = F)  
# write.csv(as.character(counting$x), 'alignment_crowd_annotations/eval_questions/prednames/counting.csv', row.names = F)  


enumerating <- read.csv('alignment/enumerating_filtered.csv')
enumerating_inv <- read.csv('alignment/enumerating_inv_filtered.csv')

set.seed(51)
dbp_map <- as.character(droplevels(sample(enumerating[grep("http://dbpedia.org/ontology/", enumerating$x),], size = 42)))
set.seed(51)
dbp_map <- append(dbp_map, paste(as.character(droplevels(sample(enumerating_inv[grep("http://dbpedia.org/ontology/", 
                                                                enumerating_inv$x),], size = 33))), '_inv', sep=''))

set.seed(51)
dbp_raw <- as.character(droplevels(sample(enumerating[grep("http://dbpedia.org/property/", enumerating$x),], size = 53)))
set.seed(51)
dbp_raw <- append(dbp_raw, paste(as.character(droplevels(sample(enumerating_inv[grep("http://dbpedia.org/property/", 
                                                                enumerating_inv$x),], size = 22))), '_inv', sep=''))

set.seed(51)
wd <- as.character(droplevels(sample(enumerating[grep("http://www.wikidata.org/prop/direct", enumerating$x),], size = 32)))
set.seed(51)
wd <- append(wd, paste(as.character(droplevels(sample(enumerating_inv[grep("http://www.wikidata.org/prop/direct", 
                                                      enumerating_inv$x),], size = 43))), '_inv', sep=''))

set.seed(51)
fb <- as.character(droplevels(sample(enumerating[grep("http://rdf.freebase.com/", enumerating$x),], size = 61)))
set.seed(51)
fb <- append(fb, paste(as.character(droplevels(sample(enumerating_inv[grep("http://rdf.freebase.com/", 
                                                      enumerating_inv$x),], size = 14))), '_inv', sep=''))

data <- append(dbp_map, append(dbp_raw, append(wd, fb)))
write.csv(data, 'alignment_crowd_annotations/eval_questions/prednames/enumerating.csv', row.names = F)  
  # write.csv(append(as.character(enumerating$x), paste(as.character(enumerating_inv$x), '_inv', sep=' ')), 
          # 'alignment_crowd_annotations/eval_questions/prednames/enumerating.csv', row.names = F)  

    # data <- append(dbp_map, append(dbp_raw, append(wd, fb)))
# write.csv(data, 'alignment_crowd_annotations/eval_questions/prednames/enumerating_inv.csv', row.names = F)  
