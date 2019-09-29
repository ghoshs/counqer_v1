setwd('/home/shrestha/Documents/Thesis/counqer')
library(dplyr)

# path = 'evaluation/enumerating/'

get_mean_ndcg <- function(path, type){
  fname = list.files(path)
  for(i in 1:length(fname)){
    dcg = read.csv(paste(path, fname[i], sep=''))
    metric = gsub('([[:alpha:]]*_)+([[:alnum:]]*)\\.csv', '\\2', fname[i])
    colnames(dcg)[3:4] <- c('pos', 'dcg')
    if (type=='EtoC') {
      dcg <- dcg[which(dcg$predE %in% GT_etoc$Input.predE),]
    } else {
      dcg <- dcg[which(dcg$predC %in% GT_ctoe$Input.predC),]
    }
    dcg$ndcg[is.na(dcg$ndcg)] <- 0
    ndcg = dcg[,c(1,2,3,10)] %>% group_by(pos) %>% summarise(mean_ndcg = mean(ndcg))
    colnames(ndcg) <- c('pos', metric)
    if (i == 1){
      data = ndcg
    } else {
      data <- full_join(data, ndcg, by=('pos'))
    }
  }
  return(data)
}
GT_etoc <- read.csv('alignment_crowd_annotations/eval_annotations/EtoC_GT_scores.csv')
GT_ctoe <- read.csv('alignment_crowd_annotations/eval_annotations/CtoE_GT_scores.csv')

dataE <- get_mean_ndcg('evaluation/t_50_e_50/enumerating/', 'EtoC')
dataC <- get_mean_ndcg('evaluation/t_50_e_50/counting/', 'CtoE')

dataE <- dataE[order(dataE$pos),]
dataC <- dataC[order(dataC$pos),]

write.csv(dataE[c(1:15),], paste('evaluation/t_50_e_50/enumerating/', 'mean_ndcg.csv', sep=''), row.names = F)
write.csv(dataC[c(1:15),], paste('evaluation/t_50_e_50/counting/', 'mean_ndcg.csv', sep=''), row.names = F)
    