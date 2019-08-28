setwd('/local/home/shrestha/Documents/Thesis/counqer')

predC <- read.csv('classifier/counting/predictions.csv')
# predC$final <- ifelse(predC$linear+predC$bayesian+predC$neural+predC$lasso > 2, 1, 
                      # ifelse(predC$linear+predC$bayesian+predC$neural+predC$lasso < 2, 0, 0.5))
predC <- predC[which(predC$lasso == 1),]
write.csv(predC[, c(1)], 'alignment/counting.csv', row.names = F)

predE <- read.csv('classifier/enumerating/predictions.csv')
# predE$final <- ifelse(predE$linear+predE$bayesian+predE$neural+predE$lasso > 2, 1, 
                      # ifelse(predE$linear+predE$bayesian+predE$neural+predE$lasso < 2, 0, 0.5))
predE <- predE[which(predE$linear == 1),]
write.csv(predE[, c(1)], 'alignment/enumerating.csv', row.names = F)
