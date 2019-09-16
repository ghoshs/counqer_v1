setwd('/local/home/shrestha/Documents/Thesis/counqer')

library(tidyr)
index = 3
fname = c('alignment_crowd_annotations/test_questions/batch_results/dbp_Batch_3758720_batch_results.csv',
          'alignment_crowd_annotations/test_questions/batch_results/wd_Batch_3760758_batch_results.csv',
          'alignment_crowd_annotations/test_questions/batch_results/dbp_Batch_3766212_batch_results.csv',
          'alignment_crowd_annotations/test_questions/batch_results/wd_Batch_3766214_batch_results.csv')

test <- read.csv(fname[index])
# test <- rbind(test, read.csv(fname[index+1]))
colnames(test)

test[which(test[,c(37)] == 'false'), c(37)] <- NA
test[which(test[,c(38)] == 'false'), c(38)] <- NA
test[which(test[,c(39)] == 'false'), c(39)] <- NA
test[which(test[,c(40)] == 'false'), c(40)] <- NA
test[which(test[,c(41)] == 'false'), c(41)] <- NA
test[which(test[,c(42)] == 'false'), c(42)] <- NA
test[which(test[,c(43)] == 'false'), c(43)] <- NA
if (index == 1){
  test[which(test[,c(44)] == 'false'), c(44)] <- NA
  test[which(test[,c(45)] == 'false'), c(45)] <- NA  
}

test.long <- test %>% gather(topicality, answer, Answer.high.High:Answer.none.None, na.rm=T)

if (index==1){
  test.long <- test.long[, -c(42,43,45)]  
} else {
  test.long <- test.long[, -c(40,41,43)]  
}

colnames(test.long)
test.long <- test.long %>% gather(enumeration, answer, 
                                     Answer.exact.and.complete.Exact.and.complete:Answer.unrelated.Unrelated, na.rm=T)
test.long <- test.long[, -c(3:15,17:23,25:27,39)]
test.long$topicality <- sapply(test.long$topicality, function (x) substr(x, tail(gregexpr("\\.",x)[[1]],1)+1, nchar(x)))
test.long$enumeration <- sapply(test.long$enumeration, function (x) substr(x, tail(gregexpr("\\.[A-Z]",x)[[1]],1)+1, nchar(x)))
test.long$enumeration <- gsub('\\.', ' ', test.long$enumeration)

test.long$topicality.match <- ifelse(as.character(test.long$Input.topicality) == test.long$topicality,1,0)
test.long$enumeration.match <- ifelse(as.character(test.long$Input.enumeration) == test.long$enumeration,1,0)

test.long %>% group_by(WorkerId) %>% summarise(n = n(), topic.n = sum(topicality.match == 1), enum.n = sum(enumeration.match==1))
      