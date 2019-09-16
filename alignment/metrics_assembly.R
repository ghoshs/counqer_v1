setwd('/local/home/shrestha/Documents/Thesis/counqer')

library(dplyr)
index = 8
pairs.fname = c('alignment/cooccurrence/dbp_map_predicate_pairs.csv', 'alignment/cooccurrence/dbp_raw_predicate_pairs.csv',
          'alignment/cooccurrence/wd_predicate_pairs.csv', 'alignment/cooccurrence/fb_predicate_pairs.csv',
          'alignment/cooccurrence/dbp_map_inv_predicate_pairs.csv', 'alignment/cooccurrence/dbp_raw_inv_predicate_pairs.csv',
          'alignment/cooccurrence/wd_inv_predicate_pairs.csv', 'alignment/cooccurrence/fb_inv_predicate_pairs.csv')
kb.pairs <- read.csv(pairs.fname[index])
kb.pairs <- kb.pairs[which(kb.pairs$count >= 50),]

cooccur.fname = c('alignment/metrics_all/dbp_map_cooccur_alignment.csv', 'alignment/metrics_all/dbp_raw_cooccur_alignment.csv',
                  'alignment/metrics_all/wd_cooccur_alignment.csv', 'alignment/metrics_all/fb_cooccur_alignment.csv',
                  'alignment/metrics_all/dbp_map_inv_cooccur_alignment.csv', 'alignment/metrics_all/dbp_raw_inv_cooccur_alignment.csv',
                  'alignment/metrics_all/wd_inv_cooccur_alignment.csv', 'alignment/metrics_all/fb_inv_cooccur_alignment.csv')
kb.cooccur.m <- read.csv(cooccur.fname[index])

prefix = c("http://dbpedia.org/ontology/", "http://dbpedia.org/property/", "http://www.wikidata.org/prop/direct/", 
           "(http://rdf.freebase.com/ns/|http://rdf.freebase.com/key/)",
           "http://dbpedia.org/ontology/", "http://dbpedia.org/property/", "http://www.wikidata.org/prop/direct/", 
           "(http://rdf.freebase.com/ns/|http://rdf.freebase.com/key/)")

if(index == 4 | index == 8){
  kb.pairs <-kb.pairs[which(startsWith(as.character(kb.pairs$predE), 'http://rdf.freebase.com/') & 
                              startsWith(as.character(kb.pairs$predC), 'http://rdf.freebase.com/')),]
  kb.cooccur.m <- kb.cooccur.m[which(!(startsWith(as.character(kb.cooccur.m$predC), 'rdf-schema') | 
                                         startsWith(as.character(kb.cooccur.m$predC), 'owl#') |
                                         startsWith(as.character(kb.cooccur.m$predE), 'rdf-schema') | 
                                         startsWith(as.character(kb.cooccur.m$predE), 'owl#')
                                       )),]
}
sum(sub(prefix[index], "", kb.pairs$predE) == kb.cooccur.m$predE) == nrow(kb.cooccur.m)
sum(sub(prefix[index], "", kb.pairs$predC) == kb.cooccur.m$predC) == nrow(kb.cooccur.m)

kb.cooccur.m$predE <- kb.pairs$predE
kb.cooccur.m$predC <- kb.pairs$predC

write.csv(kb.cooccur.m, cooccur.fname[index], row.names = F)

# keep only required metrics
count <- read.csv('alignment/counting_filtered.csv')
enum_inv <- read.csv('alignment/enumerating_inv_filtered.csv')
enum <- read.csv('alignment/enumerating_filtered.csv')
kb.cooccur.m <- read.csv(cooccur.fname[1])
kb.cooccur.m <- rbind(kb.cooccur.m, read.csv(cooccur.fname[2]))
kb.cooccur.m <- rbind(kb.cooccur.m, read.csv(cooccur.fname[3]))
kb.cooccur.m <- rbind(kb.cooccur.m, read.csv(cooccur.fname[4]))
kb.cooccur.m.req <- kb.cooccur.m[which(kb.cooccur.m$predE %in% enum$x & kb.cooccur.m$predC %in% count$x),]
kb.cooccur.m.req$inv <- 0

kb.cooccur.m.inv <- read.csv(cooccur.fname[5])
kb.cooccur.m.inv <- rbind(kb.cooccur.m.inv, read.csv(cooccur.fname[6]))
kb.cooccur.m.inv <- rbind(kb.cooccur.m.inv, read.csv(cooccur.fname[7]))
kb.cooccur.m.inv <- rbind(kb.cooccur.m.inv, read.csv(cooccur.fname[8]))
kb.cooccur.m.inv.req <- kb.cooccur.m.inv[which(kb.cooccur.m.inv$predE %in% enum_inv$x & kb.cooccur.m.inv$predC %in% count$x),]
kb.cooccur.m.inv.req$inv <- 1

kb.cooccur.m.req <- rbind(kb.cooccur.m.req, kb.cooccur.m.inv.req)
write.csv(kb.cooccur.m.req, 'alignment/metrics_req/cooccur_alignment.csv', row.names = F)

by_enum <- kb.cooccur.m.req %>% group_by(inv, predE) %>% summarize(n=n())
sum(by_enum$n[which(by_enum$n > 2)])
length(unique(by_enum$predE)) # 709
# dbp_map 65, dbp_raw 586, wd 7, fb 105

by_count <- kb.cooccur.m.req %>% group_by(predC) %>% summarize(n=n())
sum(by_count$n[which(by_count$n > 2)])
length(unique(by_count$predC))# 684
# dbp_map 41, dbp_raw 608, wd 14, fb 21
