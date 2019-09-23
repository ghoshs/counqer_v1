setwd('/home/shrestha/Documents/Thesis/counqer')
library(dplyr)

# path = 'evaluation/enumerating/'

get_mean_ndcg <- function(path){
  fname = list.files(path)
  for(i in 1:length(fname)){
    dcg = read.csv(paste(path, fname[i], sep=''))
    metric = gsub('([[:alpha:]]*_)+([[:alnum:]]*)\\.csv', '\\2', fname[i])
    colnames(dcg)[3:4] <- c('pos', 'dcg')
    ndcg = dcg[complete.cases(dcg),] %>% group_by(pos) %>% summarise(mean_ndcg = mean(ndcg))
    colnames(ndcg) <- c('pos', metric)
    if (i == 1){
      data = ndcg
    } else {
      data <- full_join(data, ndcg, by=('pos'))
    }
  }
  return(data)
}

dataE <- get_mean_ndcg('evaluation/enumerating/')
dataC <- get_mean_ndcg('evaluation/counting/')

write.csv(dataE, paste('evaluation/enumerating/', 'mean_ndcg.csv', sep=''), row.names = F)
write.csv(dataC, paste('evaluation/counting/', 'mean_ndcg.csv', sep=''), row.names = F)
