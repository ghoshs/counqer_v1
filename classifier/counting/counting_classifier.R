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

dataC <- read.csv('feature_file/labelled_data_counting.csv')
## num data points = 400
## remove uncertain labels

dataC.1 <- dataC[which(dataC$final <= 0.4 | dataC$final >= 0.6),]
dataC.1$final[dataC.1$final < 0.5] <- 0
dataC.1$final[dataC.1$final > 0.5] <- 1

sum(dataC.1$final == 1) ## 39 positives
sum(dataC.1$final == 0) ## 310 negatives

colnames(dataC.1)

dataC.2 <- dataC.1[, c(1:13,19:23,27:29,31)]

### remove identified outliers
dataC.2 <- dataC.2[which(!(dataC.2$predicate %in% removeC.outlier)),]

pairwise_corC <- data.frame(cor(dataC.2[, -c(1, 21)]))

### data imputaion for missing values
predC.usage_ratio <- dataC.2$plural_est_matches/dataC.2$singular_est_matches
set.seed(1)
imputeC <- runif(sum(is.nan(predC.usage_ratio)))*10^-3
set.seed(1)
predC.usage_ratio[is.nan(predC.usage_ratio)] <- ifelse(sample(c(0,1), size = sum(is.nan(predC.usage_ratio)), 
                                                              replace = T, prob = c(0.5, 0.5)) == 1, 
                                                       1 - imputeC, 1 + imputeC)
dataC.2$usage_ratio <- predC.usage_ratio
### imputation by constant
# dataC.2$usage_ratio <- ifelse(dataC.2$singular_est_matches > 0, 
                              # dataC.2$plural_est_matches/dataC.2$singular_est_matches, 0)
### scale values
dataC.2[, c(2, 9:13, 19, 20)] <- lapply(dataC.2[, c(2, 9:13, 19, 20)], function(x) log10(x + 10^-5))

dataC.2[,-c(22)] <- lapply(dataC.2[, -c(22)], function(x) if (is.numeric(x)) scale(x) else {x})
# pairwise_corC.2 <- data.frame(cor(dataC.2[, -c(1, 21)]))

### plot/cor highly correlated variables (> 0.5 or < -0.5) in different ranges
colnames(dataC.2)
plot(dataC.2$pcent_int, dataC.2$pcent_unk)
plot(dataC.2$numeric_10_ptile, dataC.2$numeric_90_ptile)
plot(dataC.2$usage_ratio, dataC.2$pcent_int)

### check variable distribution
ggplot(dataC.2, aes(x=frequency)) + geom_histogram()
ggplot(dataC.2, aes(y=numeric_max, x=as.factor(final))) + geom_boxplot()
ggplot(dataC.2, aes(y=numeric_avg, x=as.factor(final))) + geom_boxplot()
ggplot(dataC.2, aes(y=numeric_10_ptile, x=as.factor(final))) + geom_boxplot()
ggplot(dataC.2, aes(y=numeric_90_ptile, x=as.factor(final))) + geom_boxplot()
ggplot(dataC.2, aes(y=usage_ratio, x=as.factor(final))) + geom_boxplot()

### Linear model
### remove codependent variables 
removeC <- c('predicate', 'pcent_comma_sep', 'pcent_float', 'pcent_date', 'pcent_ne', 'pcent_unk', 
             'numeric_min', 'singular_est_matches', 'plural_est_matches', 
             'persub_max_int', 'persub_min_int', 'persub_avg_int', 'persub_10_ptile_int', 'persub_90_ptile_int')

### remove outliers
dataC.2$predicate[which(dataC.2$usage_ratio > 5)]
dataC.2$predicate[which(dataC.2$numeric_max > 15)]
removeC.outlier <- c('http://dbpedia.org/property/truckWins', 'http://dbpedia.org/ontology/virtualChannel', 
                     'http://dbpedia.org/property/casNumber', 'http://www.wikidata.org/prop/direct/P1181')
## if removeC.outlier is not empty, remove outliers and rescale data line 46

train.dataC <- dataC.2[!names(dataC.2) %in% removeC]
# train.dataC$final <- as.factor(train.dataC$final)
linear.modelC <- glm(final~., data=train.dataC, family = binomial)
summary(linear.modelC)

linear.probC <- predict(linear.modelC, type = "response")
plot(linear.probC,train.dataC$final, col=as.factor(train.dataC$final))
plot(linear.probC, linear.modelC$residuals) ## residuals have a clear trend - variance in data left to be explained 

thresholdC <- seq(0,1,0.01) 
respC.linear <- get_response_df(thresholdC, train.dataC, linear.probC)
rocC.linear <- get_roc_df(thresholdC, respC.linear)

# table(respC.linear[,10], respC.linear$final)
thresholdC.linear <- rocC.linear$threshold[which(rocC.linear$distance == min(rocC.linear$distance))]
#0.11
jpeg('classifier/counting/linear_counting.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptC.linear <- rocC.linear$tpr[which(rocC.linear$threshold == thresholdC.linear)]
xintercptC.linear <- rocC.linear$fpr[which(rocC.linear$threshold == thresholdC.linear)]
ggplot(rocC.linear, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
    geom_hline(yintercept = yintercptC.linear) + geom_vline(xintercept = xintercptC.linear)
dev.off()
    
### Loocv stats
loocvC.linear = rep(0,nrow(train.dataC))
set.seed(12)
train <- seq(1, nrow(train.dataC))
for (i in 1:nrow(train.dataC)){
    tr <- train[train!=i]
    glm.fit <- glm(formula=final ~ ., data=train.dataC, subset=tr, family=binomial)
    loocvC.linear[i] = ifelse(predict(glm.fit, train.dataC[-tr,], type='response') > thresholdC.linear, 1, 0)
}
conf_matrixC.linear <- table(loocvC.linear, train.dataC$final)
conf_matrixC.linear["1","1"]/sum(train.dataC$final == 1) #recall
conf_matrixC.linear["1","1"]/(conf_matrixC.linear["1","0"] + conf_matrixC.linear["1","1"]) #precision

library(boot)
set.seed(17)
cv.error.linear.modelC <- cv.glm(train.dataC[train, ], linear.modelC)
cv.error.linear.modelC$delta[1]

### Bayesian GLM (Gelman et al. 2008)
library(arm)
bayesian.modelC <- bayesglm(final~., data = train.dataC, family="binomial")
summary(bayesian.modelC)
display(bayesian.modelC)

bayesian.probC <- predict(bayesian.modelC, type="response")
plot(bayesian.probC,train.dataC$final, col=as.factor(train.dataC$final))
r <- names(bayesian.modelC$residuals[which(bayesian.modelC$residuals < 1)])
plot(bayesian.probC, bayesian.modelC$residuals) ## residuals have a clear trend - variance in data left to be explained 
plot(bayesian.probC[r], bayesian.modelC$residuals[r]) 

thresholdC <- seq(0,1,0.01) 
respC.bayesian <- get_response_df(thresholdC, train.dataC, bayesian.probC)
rocC.bayesian <- get_roc_df(thresholdC, respC.bayesian)

thresholdC.bayesian <- rocC.bayesian$threshold[which(rocC.bayesian$distance == min(rocC.bayesian$distance))]
#0.11
jpeg('classifier/counting/bayesian_counting.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptC.bayesian <- rocC.bayesian$tpr[which(rocC.bayesian$threshold == thresholdC.bayesian)]
xintercptC.bayesian <- rocC.bayesian$fpr[which(rocC.bayesian$threshold == thresholdC.bayesian)]
ggplot(rocC.bayesian, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
    geom_hline(yintercept = yintercptC.bayesian) + geom_vline(xintercept = xintercptC.bayesian)
dev.off()

### Loocv stats
loocvC.bayesian = rep(0,nrow(train.dataC))
set.seed(12)
train <- seq(1, nrow(train.dataC))
for (i in 1:nrow(train.dataC)){
    tr <- train[train!=i]
    bayesian.fit <- bayesglm(formula=final ~ ., data=train.dataC[tr,], family=binomial)
    loocvC.bayesian[i] = ifelse(predict(bayesian.fit, train.dataC[-tr,], type='response') > thresholdC.bayesian, 1, 0)
}
conf_matrixC.bayes <- table(loocvC.bayesian, train.dataC$final)
conf_matrixC.bayes["1","1"]/sum(train.dataC$final == 1) #recall
conf_matrixC.bayes["1","1"]/(conf_matrixC.bayes["1","0"] + conf_matrixC.bayes["1","1"]) #precision

library(boot)
set.seed(17)
cv.error.bayes.modelC <- cv.glm(train.dataC[train, ], bayesian.modelC)
cv.error.bayes.modelC$delta[1]

### Neuralnets
library(neuralnet)
library(tidyr)
neural.train.dataC <- train.dataC %>% mutate(temp = 1) %>% spread(sub_type, temp, fill=0)
set.seed(12)
train <- sample(nrow(neural.train.dataC), nrow(neural.train.dataC))
set.seed(12)
nn.modelC = neuralnet(final~., data=neural.train.dataC, hidden=3, act.fct = "logistic", linear.output = F)
plot(nn.modelC)
neural.probC <- compute(nn.modelC, neural.train.dataC)$net.result
# neural.probC <- (compute(nn.modelC, neural.train.dataC)$net.result + 1)*0.5
plot(neural.probC,neural.train.dataC$final, col=as.factor(neural.train.dataC$final))
plot(neural.probC, (neural.train.dataC$final-neural.probC)) ## residuals have a clear trend - variance in data left to be explained 

thresholdC <- seq(0,1,0.01) 
respC.neural <- get_response_df(thresholdC, neural.train.dataC, neural.probC[,1])
rocC.neural <- get_roc_df(thresholdC, respC.neural)

thresholdC.neural <- rocC.neural$threshold[which(rocC.neural$distance == min(rocC.neural$distance))][1]
#0.11
jpeg('classifier/counting/neural_counting.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptC.neural <- rocC.neural$tpr[which(rocC.neural$threshold == thresholdC.neural)]
xintercptC.neural <- rocC.neural$fpr[which(rocC.neural$threshold == thresholdC.neural)]
ggplot(rocC.neural, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
    geom_hline(yintercept = yintercptC.neural) + geom_vline(xintercept = xintercptC.neural)
dev.off()

### Loocv stats
conf_matrixC.neural <- table(ifelse(neural.probC > thresholdC.neural, 1, 0), neural.train.dataC$final)
conf_matrixC.neural["1","1"]/sum(neural.train.dataC$final == 1) #recall
conf_matrixC.neural["1","1"]/(conf_matrixC.neural["1","0"] + conf_matrixC.neural["1","1"]) #precision

### Lasso
library(glmnet)
grid =10^seq(10,-2, length =100)
x <- model.matrix(final~., train.dataC)
y <- train.dataC$final
lasso.modelC <- glmnet(x, y, alpha=1, lambda=grid)
plot(lasso.modelC, col=1:20, label=TRUE)
legend("bottomleft", title="Predictors", colnames(x), fill=1:8, cex=0.75)

set.seed (1)
cv.out.lasso <- cv.glmnet(x,y,alpha =1)
# plot(cv.out.lasso)
bestlamC <- cv.out.lasso$lambda.min
lasso.probC <- predict(lasso.modelC ,s=bestlamC ,newx=x)
plot(lasso.probC,y, col=as.factor(train.dataC$final))
plot(lasso.probC, y - lasso.probC) ## residuals have a clear trend - variance in data left to be explained 

thresholdC <- seq(0,1,0.01) 
respC.lasso <- get_response_df(thresholdC, train.dataC, lasso.probC[,1])
rocC.lasso <- get_roc_df(thresholdC, respC.lasso)

thresholdC.lasso <- rocC.lasso$threshold[which(rocC.lasso$distance == min(rocC.lasso$distance))][1]
#0.11
jpeg('classifier/counting/lasso_counting.jpg', width = 10, height = 10, units = 'in', res=300)
yintercptC.lasso <- rocC.lasso$tpr[which(rocC.lasso$threshold == thresholdC.lasso)]
xintercptC.lasso <- rocC.lasso$fpr[which(rocC.lasso$threshold == thresholdC.lasso)]
ggplot(rocC.lasso, aes(x=fpr, y=tpr)) + geom_point() + geom_smooth() + 
    geom_hline(yintercept = yintercptC.lasso) + geom_vline(xintercept = xintercptC.lasso)
dev.off()

### Loocv stats
loocvC.lasso = rep(0,nrow(train.dataC))
set.seed(12)
train <- seq(1, nrow(train.dataC))
for (i in 1:nrow(train.dataC)){
    tr <- train[train!=i]
    lasso.fit <- glmnet(x[tr,], y[tr], alpha = 1, lambda = grid)
    cv.lasso.fit <- cv.glmnet(x[tr,], y[tr], alpha=1)
    loocvC.lasso[i] = ifelse(predict(lasso.fit, cv.lasso.fit$lambda.min, 
                                     newx=matrix(x[-tr,], ncol= ncol(x)))[,1] > thresholdC.lasso, 1, 0)
}
conf_matrixC.lasso <- table(ifelse(lasso.probC > thresholdC.lasso, 1, 0), train.dataC$final)
conf_matrixC.lasso["1","1"]/sum(train.dataC$final == 1) #recall
conf_matrixC.lasso["1","1"]/(conf_matrixC.lasso["1","0"] + conf_matrixC.lasso["1","1"]) #precision

### SVM
library(e1071)
svm.train.dataC <- data.frame(x=model.matrix(final~., neural.train.dataC), y=as.factor(neural.train.dataC$final))
cv.svm.modelC <- tune(svm, y~., data=svm.train.dataC, kernel="radial", scale=F,
                      ranges = c(10^-6, 10^-5, 10^-4, 0.001, 0.01, 0.1, 1))
summary(cv.svm.modelC)

### compare models
jpeg('classifier/counting/model_comparison_counting', width = 10, height = 10, units = 'in', res=300)
ggplot() + 
    geom_point(data=rocC.linear, aes(x=fpr, y=tpr), fill="blue", color="blue") + 
    geom_smooth(data=rocC.linear, aes(x=fpr, y=tpr), fill="blue", color="blue") + 
    geom_point(data=rocC.bayesian, aes(x=fpr, y=tpr), fill="red", color="red") + 
    geom_smooth(data=rocC.bayesian, aes(x=fpr, y=tpr), fill="red", color="red") +
    geom_point(data=rocC.neural, aes(x=fpr, y=tpr),  fill="green", color="green") +
    geom_smooth(data=rocC.neural, aes(x=fpr, y=tpr), fill="green", color="green") +
    geom_point(data=rocC.lasso, aes(x=fpr, y=tpr),  fill="yellow", color="yellow") + 
    geom_smooth(data=rocC.lasso, aes(x=fpr, y=tpr), fill="yellow", color="yellow")
dev.off()


### application with best model
test.dataC <- read.csv('feature_file/predicates_p_50.csv', stringsAsFactors = F, na.strings = "NULL")
test.dataC <- test.dataC[, c(1:13,19:23,27:29)]
test.dataC[is.na(test.dataC)] <- 0

### scale values
test.dataC$usage_ratio <- ifelse(test.dataC$singular_est_matches > 0, 
                              test.dataC$plural_est_matches/test.dataC$singular_est_matches, 0)
test.dataC[, c(2, 9:13, 19, 20)] <- lapply(test.dataC[, c(2, 9:13, 19, 20)], function(x) log10(x + 10^-5))

test.dataC[] <- lapply(test.dataC, function(x) if (is.numeric(x)) scale(x) else {x})
# pairwise_corC.2 <- data.frame(cor(dataC.2[, -c(1, 21)]))

### remove codependent variables 
removeC <- c('pcent_comma_sep', 'pcent_float', 'pcent_date', 'pcent_ne', 'pcent_unk', 
             'numeric_min', 'singular_est_matches', 'plural_est_matches', 
             'persub_max_int', 'persub_min_int', 'persub_avg_int', 'persub_10_ptile_int', 'persub_90_ptile_int')
test.dataC <- test.dataC[!names(test.dataC) %in% removeC]
neural.test.dataC <- test.dataC %>% mutate(temp = 1) %>% spread(sub_type, temp, fill=0)
lasso.test.dataC <- model.matrix(predicate~., test.dataC)

predictionsC <- data.frame(matrix(nrow = nrow(test.dataC), ncol = 5))
colnames(predictionsC) <- c("predicate","linear", "bayesian", "neural", "lasso")
predictionsC$predicate <- test.dataC$predicate
predictionsC$linear <- predict(linear.modelC, newdata = test.dataC, type = "response")
predictionsC$bayesian <- predict(bayesian.modelC, newdata = test.dataC, type="response")
predictionsC$neural <- compute(nn.modelC, neural.test.dataC)$net.result[,1]
predictionsC$lasso <- predict(lasso.modelC, s=bestlamC ,newx=lasso.test.dataC)[,1]
