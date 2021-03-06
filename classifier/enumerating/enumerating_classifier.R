setwd('/local/home/shrestha/Documents/Thesis/counqer')
library(dplyr)
library(ggplot2)
library(ggiraph)
library(ggiraphExtra)
library(plyr)

get_response_df <- function(threshold, train.data, probability) {
  response <- matrix(ncol = nrow(train.data), nrow = 0)
  for(i in seq(1, length(threshold), 1)){
    response <- rbind(response, ifelse(probability >= threshold[i], 1, 0))
  }
  response <- as.data.frame(t(response))
  response$final <- train.data$final
  return (response)
}

get_roc_df <- function(threshold, response_df) {
  roc <- data.frame(matrix(nrow = length(threshold), ncol = 4))    
  colnames(roc) <- c('threshold','tpr', 'fpr', 'distance')
  for(i in seq(1,length(threshold),1)){
    temp <- table(response_df[,i], response_df$final)
    roc[i, "threshold"] <- threshold[i]
    roc[i, "tpr"] <- ifelse("1" %in% rownames(temp), temp["1","1"]/sum(response_df$final == 1), 0)
    roc[i, "fpr"] <- ifelse("1" %in% rownames(temp), temp["1","0"]/sum(response_df$final == 0), 0)
    roc[i, "distance"] <- sqrt((1 - roc[i, "tpr"])^2 + (0 - roc[i, "fpr"])^2)
  }
  return(roc)
}

dataE <- read.csv('feature_file/labelled_data_enumerating.csv')
## num data points = 400
## remove uncertain labels
dataE.1 <- dataE[which(dataE$final <= 0.4 | dataE$final >= 0.6),]
dataE.1$final[dataE.1$final < 0.5] <- 0
dataE.1$final[dataE.1$final > 0.5] <- 1

sum(dataE.1$final == 1) ## 135 positives
sum(dataE.1$final == 0) ## 198 negatives

colnames(dataE.1)

dataE.2 <- dataE.1[, c(1:8,14:18,27:31)]
### remove identified outliers
dataE.2 <- dataE.2[which(!(dataE.2$predicate %in% removeE.outlier)),]
pairwise_corE <- data.frame(cor(dataE.2[, -c(1, 16, 17)]))

### data imputaion for missing values
predE.usage_ratio <- dataE.2$plural_est_matches/dataE.2$singular_est_matches
set.seed(1)
imputeE <- runif(sum(is.nan(predE.usage_ratio)))*10^-3
set.seed(1)
predE.usage_ratio[is.nan(predE.usage_ratio)] <- ifelse(sample(c(0,1), size = sum(is.nan(predE.usage_ratio)), 
                                                              replace = T, prob = c(0.5, 0.5)) == 1, 
                                                       1 - imputeE, 1 + imputeE)
dataE.2$usage_ratio <- predE.usage_ratio
### imputation by constant
# dataE.2$usage_ratio <- ifelse(dataE.2$singular_est_matches > 0, 
#                               dataE.2$plural_est_matches/dataE.2$singular_est_matches, 0)

### scale values
dataE.2[, c(2, 14, 15)] <- lapply(dataE.2[, c(2, 14, 15)], function(x) log10(x + 10^-5))
dataE.2[, -c(18)] <- lapply(dataE.2[, -c(18)],  function(x) if (is.numeric(x)) scale(x) else {x})

### plot/cor highly correlated variables (> 0.5 or < -0.5) in different ranges
plot(dataE.2$pcent_comma_sep, dataE.2$pcent_ne)
plot(dataE.2$persub_90_ptile_ne, dataE.2$persub_min_ne)

### check variable distribution
ggplot(dataE.2, aes(x=frequency)) + geom_histogram()
ggplot(dataE.2, aes(y=usage_ratio, x=as.factor(final))) + geom_boxplot()

### Linear model
### remove codependent variables 
removeE <- c('predicate', 'pcent_comma_sep', 'pcent_int', 'pcent_float', 'pcent_date', 'pcent_unk', 
             'singular_est_matches', 'plural_est_matches', 
             'persub_max_ne', 'persub_min_ne', 'persub_10_ptile_ne', 'persub_avg_ne')

### remove outliers
dataE.2$predicate[which(dataE.2$usage_ratio > 5)]
dataE.2$predicate[which(dataE.2$persub_90_ptile_ne > 8)]
removeE.outlier <- c('http://dbpedia.org/ontology/stateOfOrigin', 'http://dbpedia.org/ontology/headEhef',
                     'http://dbpedia.org/ontology/principalEngineer', 'http://www.wikidata.org/prop/direct/P3489',
                     'http://rdf.freebase.com/ns/base.vermont.vermont_fresh_network_partner_type.partner',
                     'http://rdf.freebase.com/ns/aviation.airline_alliance.member_airlines')
## if removeE.outlier is not empty, remove outliers and rescale data line 46

train.dataE <- dataE.2[!names(dataE.2) %in% removeE]
train.dataE$sub_type <- as.factor(sub("^", "sub.", train.dataE$sub_type))
train.dataE$obj_type <- as.factor(sub("^", "obj.", train.dataE$obj_type))

linear.modelE <- glm(final~., data=train.dataE, family = binomial)
summary(linear.modelE)

linear.probE <- predict(linear.modelE, type = "response")
plot(linear.probE, train.dataE$final)
plot(linear.probE, linear.modelE$residuals) ## residuals have a clear trend - variance in data left to be explained 

thresholdE <- seq(0,1,0.01) 
respE.linear <- get_response_df(thresholdE, train.dataE, linear.probE)
rocE.linear <- get_roc_df(thresholdE, respE.linear)

thresholdE.linear <- rocE.linear$threshold[which(rocE.linear$distance == min(rocE.linear$distance))][1]
# 0.4
jpeg('classifier/enumerating/linear_enumerating.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptE.linear <- rocE.linear$tpr[which(rocE.linear$threshold == thresholdE.linear)]
xintercptE.linear <- rocE.linear$fpr[which(rocE.linear$threshold == thresholdE.linear)]
ggplot(rocE.linear, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
  geom_hline(yintercept = yintercptE.linear) + geom_vline(xintercept = xintercptE.linear)
dev.off()

### Loocv stats
loocvE.linear = rep(0,nrow(train.dataE))
set.seed(12)
train <- seq(1, nrow(train.dataE))
for (i in 1:nrow(train.dataE)){
  tr <- train[train!=i]
  glm.fit <- glm(formula=final ~ ., data=train.dataE, subset=tr, family=binomial)
  loocvE.linear[i] = ifelse(predict(glm.fit, train.dataE[-tr,], type='response') > thresholdE.linear, 1, 0)
}
conf_matrixE.linear <- table(loocvE.linear, train.dataE$final)
conf_matrixE.linear["1","1"]/sum(train.dataE$final == 1) #recall
conf_matrixE.linear["1","1"]/(conf_matrixE.linear["1","0"] + conf_matrixE.linear["1","1"]) #precision

library(boot)
set.seed(17)
cv.error.linear.modelE <- cv.glm(train.dataE[train, ], linear.modelE)
cv.error.linear.modelE$delta[1]

### Bayesian GLM (Gelman et al. 2008)
library(arm)
bayesian.modelE <- bayesglm(final~., data = train.dataE, family="binomial")
summary(bayesian.modelE)

bayesian.probE <- predict(bayesian.modelE, type="response")
plot(bayesian.probE,train.dataE$final, col=as.factor(train.dataE$final))
plot(bayesian.probE, bayesian.modelE$residuals) ## residuals have a clear trend - variance in data left to be explained 

thresholdE <- seq(0,1,0.01) 
respE.bayesian <- get_response_df(thresholdE, train.dataE, bayesian.probE)
rocE.bayesian <- get_roc_df(thresholdE, respE.bayesian)

thresholdE.bayesian <- rocE.bayesian$threshold[which(rocE.bayesian$distance == min(rocE.bayesian$distance))][1]
#0.41
jpeg('classifier/enumerating/bayesian_enumerating.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptE.bayesian <- rocE.bayesian$tpr[which(rocE.bayesian$threshold == thresholdE.bayesian)]
xintercptE.bayesian <- rocE.bayesian$fpr[which(rocE.bayesian$threshold == thresholdE.bayesian)]
ggplot(rocE.bayesian, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
  geom_hline(yintercept = yintercptE.bayesian) + geom_vline(xintercept = xintercptE.bayesian)
dev.off()


### Loocv stats
loocvE.bayesian = rep(0,nrow(train.dataE))
set.seed(12)
train <- seq(1, nrow(train.dataE))
for (i in 1:nrow(train.dataE)){
  tr <- train[train!=i]
  bayesian.fit <- bayesglm(formula=final ~ ., data=train.dataE[tr,], family=binomial)
  loocvE.bayesian[i] = ifelse(predict(bayesian.fit, train.dataE[-tr,], type='response') > thresholdE.bayesian, 1, 0)
}
conf_matrixE.bayes <- table(loocvE.bayesian, train.dataE$final)
conf_matrixE.bayes["1","1"]/sum(train.dataE$final == 1) #recall
conf_matrixE.bayes["1","1"]/(conf_matrixE.bayes["1","0"] + conf_matrixE.bayes["1","1"]) #precision

library(boot)
set.seed(17)
cv.error.bayes.modelE <- cv.glm(train.dataE[train, ], bayesian.modelE)
cv.error.bayes.modelE$delta[1]

### Neuralnets
library(neuralnet)
library(tidyr)
neural.train.dataE <- train.dataE %>% mutate(temp = 1) %>% spread(sub_type, temp, fill=0)
neural.train.dataE <- neural.train.dataE %>% mutate(temp = 1) %>% spread(obj_type, temp, fill=0)
set.seed(12)
train <- sample(nrow(neural.train.dataE), nrow(neural.train.dataE))
set.seed(12)
nn.modelE = neuralnet(final~., data=neural.train.dataE, hidden=3, act.fct = "logistic", linear.output = F, rep=10)
plot(nn.modelE)
neural.probE <- compute(nn.modelE, neural.train.dataE, rep=which.min(nn.modelE$result.matrix[1,]))$net.result

thresholdE <- seq(0,1,0.01) 
respE.neural <- get_response_df(thresholdE, neural.train.dataE, neural.probE[,1])
rocE.neural <- get_roc_df(thresholdE, respE.neural)

thresholdE.neural <- rocE.neural$threshold[which(rocE.neural$distance == min(rocE.neural$distance))][1]
# 0.43
jpeg('classifier/enumerating/neural_enumerating.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptE.neural <- rocE.neural$tpr[which(rocE.neural$threshold == thresholdE.neural)]
xintercptE.neural <- rocE.neural$fpr[which(rocE.neural$threshold == thresholdE.neural)]
ggplot(rocE.neural, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
  geom_hline(yintercept = yintercptE.neural) + geom_vline(xintercept = xintercptE.neural)
dev.off()

### Loocv stats
loocvE.neural = rep(0,nrow(train.dataE))
set.seed(12)
train <- seq(1, nrow(train.dataE))
for (i in 1:nrow(train.dataE)){
  tr <- train[train!=i]
  nn.fit = neuralnet(final~., data=neural.train.dataE[tr,], hidden=3, act.fct = "logistic", linear.output = F, rep=10)
  loocvE.neural[i] = ifelse(compute(nn.fit, neural.train.dataE, 
                                    rep=which.min(nn.fit$result.matrix[1,]))$net.result[-tr,1] > thresholdE.neural, 1, 0)
}
conf_matrixE.neural <- table(ifelse(loocvE.neural > thresholdE.neural, 1, 0), neural.train.dataE$final)
conf_matrixE.neural["1","1"]/sum(neural.train.dataE$final == 1) #recall
conf_matrixE.neural["1","1"]/(conf_matrixE.neural["1","0"] + conf_matrixE.neural["1","1"]) #precision

### Lasso
library(glmnet)
grid =10^seq(10,-2, length =100)
x <- model.matrix(final~., train.dataE)
y <- train.dataE$final
lasso.modelE <- glmnet(x, y, alpha=1, lambda=grid)
plot(lasso.modelE, col=1:20, label=TRUE)
legend("bottomleft", title="Predictors", colnames(x), fill=1:8, cex=0.75)

set.seed (1)
cv.out.lasso.modelE <- cv.glmnet(x,y,alpha =1)
# plot(cv.out.lasso)
bestlamE <- cv.out.lasso.modelE$lambda.min
lasso.probE <- predict(lasso.modelE ,s=bestlamE ,newx=x)
plot(lasso.probE, y, col=as.factor(train.dataE$final))
plot(lasso.probE, y - lasso.probE) ## residuals have a clear trend - variance in data left to be explained 

thresholdE <- seq(0,1,0.01) 
respE.lasso <- get_response_df(thresholdE, train.dataE, lasso.probE[,1])
rocE.lasso <- get_roc_df(thresholdE, respE.lasso)

thresholdE.lasso <- rocE.lasso$threshold[which(rocE.lasso$distance == min(rocE.lasso$distance))][1]
#0.4
jpeg('classifier/enumerating/lasso_enumerating.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptE.lasso <- rocE.lasso$tpr[which(rocE.lasso$threshold == thresholdE.lasso)]
xintercptE.lasso <- rocE.lasso$fpr[which(rocE.lasso$threshold == thresholdE.lasso)]
ggplot(rocE.lasso, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
  geom_hline(yintercept = yintercptE.lasso) + geom_vline(xintercept = xintercptE.lasso)
dev.off()

### Loocv stats
loocvE.lasso = rep(0,nrow(train.dataE))
set.seed(12)
train <- seq(1, nrow(train.dataE))
for (i in 1:nrow(train.dataE)){
  tr <- train[train!=i]
  lasso.fit <- glmnet(x[tr,], y[tr], alpha = 1, lambda = grid)
  cv.lasso.fit <- cv.glmnet(x[tr,], y[tr], alpha=1)
  loocvE.lasso[i] = ifelse(predict(lasso.fit, cv.lasso.fit$lambda.min, 
                                   newx=matrix(x[-tr,], ncol= ncol(x)))[,1] > thresholdE.lasso, 1, 0)
}
conf_matrixE.lasso <- table(ifelse(lasso.probE > thresholdE.lasso, 1, 0), train.dataE$final)
conf_matrixE.lasso["1","1"]/sum(train.dataE$final == 1) #recall
conf_matrixE.lasso["1","1"]/(conf_matrixE.lasso["1","0"] + conf_matrixE.lasso["1","1"]) #precision

  ### compare models
jpeg('classifier/enumerating/model_comparison_enumerating.jpg', width = 10, height = 10, units = 'in', res=300)
ggplot() + 
  geom_point(data=rocE.linear, aes(x=fpr, y=tpr), fill="blue", color="blue") + 
  geom_smooth(data=rocE.linear, aes(x=fpr, y=tpr), fill="blue", color="blue") + 
  geom_hline(yintercept = yintercptE.linear, color="blue") + geom_vline(xintercept = xintercptE.linear, color="blue") +
  geom_point(data=rocE.bayesian, aes(x=fpr, y=tpr), fill="red", color="red") + 
  geom_smooth(data=rocE.bayesian, aes(x=fpr, y=tpr), fill="red", color="red") +
  geom_hline(yintercept = yintercptE.bayesian, color="red") + geom_vline(xintercept = xintercptE.bayesian, color="red") +
  geom_point(data=rocE.neural, aes(x=fpr, y=tpr),  fill="green", color="green") +
  geom_smooth(data=rocE.neural, aes(x=fpr, y=tpr), fill="green", color="green") +
  geom_hline(yintercept = yintercptE.neural, color="green") + geom_vline(xintercept = xintercptE.neural, color="green") +
  geom_point(data=rocE.lasso, aes(x=fpr, y=tpr),  fill="yellow", color="yellow") + 
  geom_smooth(data=rocE.lasso, aes(x=fpr, y=tpr), fill="yellow", color="yellow") +
  geom_hline(yintercept = yintercptE.lasso, color="yellow") + geom_vline(xintercept = xintercptE.lasso, color="yellow")
dev.off()

### application with best model
test.dataE <- read.csv('feature_file/predicates_p_50.csv', na.strings = "NULL")
test.dataE <- test.dataE[, c(1:8,14:18,27:30)]
test.dataE[is.na(test.dataE)] <- 0

### data imputation for missing values
predE.usage_ratio.test <- test.dataE$plural_est_matches/test.dataE$singular_est_matches
predE.usage_ratio.test[is.infinite(predE.usage_ratio.test)] <- NaN
set.seed(1)
imputeE.test <- runif(sum(is.nan(predE.usage_ratio.test)))*10^-3
set.seed(1)
predE.usage_ratio.test[is.nan(predE.usage_ratio.test)] <- ifelse(sample(c(0,1), size = sum(is.nan(predE.usage_ratio.test)), 
                                                                        replace = T, prob = c(0.5, 0.5)) == 1, 
                                                                 1 - imputeE.test, 1 + imputeE.test)
test.dataE$usage_ratio <- predE.usage_ratio.test
# test.dataE$usage_ratio <- ifelse(test.dataE$singular_est_matches > 0, 
#                                  test.dataE$plural_est_matches/test.dataE$singular_est_matches, 0)

### scale values
test.dataE[, c(2, 14, 15)] <- lapply(test.dataE[, c(2, 14, 15)], function(x) log10(x + 10^-5))
test.dataE[] <- lapply(test.dataE,  function(x) if (is.numeric(x)) scale(x) else {x})
# pairwise_corE.2 <- data.frame(cor(dataE.2[, -c(1, 21)]))

### replace bnode by thing in sub_type and literal in obj_type
test.dataE$obj_type[which(test.dataE$obj_type == 'bnode')] <- "literal"
test.dataE$obj_type <- factor(test.dataE$obj_type)

### remove codependent variables 
removeE <- c('pcent_comma_sep', 'pcent_int', 'pcent_float', 'pcent_date', 'pcent_unk', 
             'singular_est_matches', 'plural_est_matches', 
             'persub_max_ne', 'persub_min_ne', 'persub_10_ptile_ne', 'persub_avg_ne')
test.dataE <- test.dataE[!names(test.dataE) %in% removeE]
test.dataE$sub_type <- as.factor(sub("^", "sub.", test.dataE$sub_type))
test.dataE$obj_type <- as.factor(sub("^", "obj.", test.dataE$obj_type))

neural.test.dataE <- test.dataE %>% mutate(temp = 1) %>% spread(sub_type, temp, fill=0)
neural.test.dataE <- neural.test.dataE %>% mutate(temp = 1) %>% spread(obj_type, temp, fill=0)
lasso.test.dataE <- model.matrix(predicate~., test.dataE)

predictionsE <- data.frame(matrix(nrow = nrow(test.dataE), ncol = 5))
colnames(predictionsE) <- c("predicate","linear", "bayesian", "neural", "lasso")
predictionsE$predicate <- test.dataE$predicate
predictionsE$linear <- ifelse(predict(linear.modelE, newdata = test.dataE, type = "response") > thresholdE.linear, 1, 0)
predictionsE$bayesian <- ifelse(predict(bayesian.modelE, newdata = test.dataE, type="response") > thresholdE.bayesian, 1, 0)
predictionsE$neural <- ifelse(compute(nn.modelE, neural.test.dataE)$net.result[,1] > thresholdE.neural, 1, 0)
predictionsE$lasso <- ifelse(predict(lasso.modelE, s=bestlamE, newx=lasso.test.dataE)[,1] > thresholdE.lasso, 1, 0)

write.csv(predictionsE, 'classifier/enumerating/predictions.csv', row.names = F)

###### Inverse predicates
test.dataE.inv <- read.csv('feature_file/inv_predicates_p_50.csv', na.strings = "NULL")
test.dataE.inv <- test.dataE.inv[, c(1:7,11:14)]
test.dataE.inv[is.na(test.dataE.inv)] <- 0
### data imputation for missing values
predE.inv.usage_ratio.test <- test.dataE.inv$plural_est_matches/test.dataE.inv$singular_est_matches
predE.inv.usage_ratio.test[is.infinite(predE.inv.usage_ratio.test)] <- NaN
set.seed(1)
imputeE.inv.test <- runif(sum(is.nan(predE.inv.usage_ratio.test)))*10^-3
set.seed(1)
predE.inv.usage_ratio.test[is.nan(predE.inv.usage_ratio.test)] <- ifelse(sample(c(0,1), 
                                                                        size = sum(is.nan(predE.inv.usage_ratio.test)), 
                                                                        replace = T, prob = c(0.5, 0.5)) == 1, 
                                                                 1 - imputeE.inv.test, 1 + imputeE.inv.test)
test.dataE.inv$usage_ratio <- predE.inv.usage_ratio.test
### scale values
test.dataE.inv[, c(7,8,9)] <- lapply(test.dataE.inv[, c(7,8,9)], function(x) log10(x + 10^-5))
test.dataE.inv[] <- lapply(test.dataE.inv,  function(x) if (is.numeric(x)) scale(x) else {x})
# ### replace bnode by thing in sub_type and literal in obj_type
# test.dataE.inv$obj_type[which(test.dataE.inv$obj_type == 'bnode')] <- "literal"
# test.dataE.inv$obj_type <- factor(test.dataE.inv$obj_type)
### remove codependent variables 
removeE <- c('singular_est_matches', 'plural_est_matches', 
             'persub_max_ne', 'persub_min_ne', 'persub_10_ptile_ne', 'persub_avg_ne')
test.dataE.inv <- test.dataE.inv[!names(test.dataE.inv) %in% removeE]

test.dataE.inv$pcent_ne <- matrix(rep(1.0, nrow(test.dataE.inv)), nrow = nrow(test.dataE.inv), ncol = 1)
colnames(test.dataE.inv)[1] <- 'predicate'
test.dataE.inv <- test.dataE.inv[,c(1,3,7,2,5,4,6)] 
test.dataE.inv$sub_type <- as.factor(sub("^", "sub.", test.dataE.inv$sub_type))
test.dataE.inv$obj_type <- as.factor(sub("^", "obj.", test.dataE.inv$obj_type))
test.dataE.inv$obj_type <- factor(test.dataE.inv$obj_type, levels = c(levels(test.dataE.inv$obj_type),"obj.literal"))

neural.test.dataE.inv <- test.dataE.inv %>% mutate(temp = 1) %>% spread(sub_type, temp, fill=0)
neural.test.dataE.inv <- neural.test.dataE.inv %>% mutate(temp = 1) %>% spread(obj_type, temp, fill=0)
if (!'obj.literal' %in% colnames(neural.test.dataE.inv)) {
  neural.test.dataE.inv$obj.literal <- 0
}
lasso.test.dataE.inv <- model.matrix(predicate~., test.dataE.inv)

predictionsE.inv <- data.frame(matrix(nrow = nrow(test.dataE.inv), ncol = 5))
colnames(predictionsE.inv) <- c("predicate","linear", "bayesian", "neural", "lasso")
predictionsE.inv$predicate <- test.dataE.inv$predicate

predictionsE.inv$linear <- ifelse(predict(linear.modelE, newdata = test.dataE.inv, type = "response") > thresholdE.linear, 1, 0)
predictionsE.inv$bayesian <- ifelse(predict(bayesian.modelE, newdata = test.dataE.inv, type="response") > thresholdE.bayesian, 1, 0)
predictionsE.inv$lasso <- ifelse(predict(lasso.modelE, s=bestlamE, newx=lasso.test.dataE.inv)[,1] > thresholdE.lasso, 1, 0)
predictionsE.inv$neural <- ifelse(compute(nn.modelE, neural.test.dataE.inv, 
                                          rep=which.min(nn.modelE$result.matrix[1,]))$net.result[,1] > thresholdE.neural, 1, 0)
write.csv(predictionsE.inv, 'classifier/enumerating/predictions_inv.csv', row.names = F)
