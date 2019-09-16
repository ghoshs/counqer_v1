setwd('/local/home/shrestha/Documents/Thesis/counqer')

library(dplyr)
f8.dbp.file <- read.csv('../msc-shrestha-ghosh/crowd_sourcing/ExpResults/f1365451_CPtoEP.csv')
f8.dbp.file <- read.csv('../msc-shrestha-ghosh/crowd_sourcing/ExpResults/f1365445_EPtoCP.csv')

colnames(f8.dbp.file)[c(17, 20)] <- c('enumeration', 'topicality')
f8.dbp.file <- f8.dbp.file[which(f8.dbp.file$X_golden == "true"),] %>% group_by(name_g, name_e, subject1, subject2, object1, object2, 
                                        topicality, enumeration) %>% summarise(n=n())

fout = 'alignment_crowd_annotations/test_questions/fig8_dbp_test.csv'
fout = 'alignment_crowd_annotations/test_questions/fig8_dbp_test2.csv'
write.csv(f8.dbp.file, fout, row.names = F)

f8.wd.file <- read.csv('../msc-shrestha-ghosh/wikidata/crowd_sourcing/ExpResults/f1365772_CPtoEP.csv')
f8.wd.file <- read.csv('../msc-shrestha-ghosh/wikidata/crowd_sourcing/ExpResults/f1365679_EPtoCP.csv')

colnames(f8.wd.file)[c(17, 20)] <- c('enumeration', 'topicality')
f8.wd.file <- f8.wd.file[which(f8.wd.file$X_golden == "true"),] %>% group_by(name_g, name_e, subject1, subject2, object1, object2, 
                                                                             topicality, enumeration) %>% summarise(n=n())
fout2 = 'alignment_crowd_annotations/test_questions/fig8_wd_test.csv'
fout2 = 'alignment_crowd_annotations/test_questions/fig8_wd_test2.csv'
write.csv(f8.wd.file, fout2, row.names = F)
