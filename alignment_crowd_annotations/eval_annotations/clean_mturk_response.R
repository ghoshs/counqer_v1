setwd('/local/home/shrestha/Documents/Thesis/counqer')

library(tidyr)

index = 1
fname = c('alignment_crowd_annotations/eval_annotations/C_to_E_Batch_3768640_batch_results.csv', 
          'alignment_crowd_annotations/eval_annotations/C_to_E_Batch_3768723_batch_results.csv',
          'alignment_crowd_annotations/eval_annotations/C_to_E_Batch_3770239_batch_results.csv',
          'alignment_crowd_annotations/eval_annotations/E_to_C_Batch_3768644_batch_results.csv', 
          'alignment_crowd_annotations/eval_annotations/E_to_C_Batch_3768731_batch_results.csv',
          'alignment_crowd_annotations/eval_annotations/E_to_C_Batch_3770245_batch_results.csv')

CtoE <- read.csv(fname[index])
CtoE <- rbind(CtoE, read.csv(fname[index+1]))
CtoE <- rbind(CtoE, read.csv(fname[index+2]))

colnames(CtoE)
CtoE <- CtoE[,c(1,24,28:34,36,39,38,40,35,37,41)]
CtoE[which(CtoE[,c(10)] == 'false'), c(10)] <- NA
CtoE[which(CtoE[,c(11)] == 'false'), c(11)] <- NA
CtoE[which(CtoE[,c(12)] == 'false'), c(12)] <- NA
CtoE[which(CtoE[,c(13)] == 'false'), c(13)] <- NA
CtoE[which(CtoE[,c(14)] == 'false'), c(14)] <- NA
CtoE[which(CtoE[,c(15)] == 'false'), c(15)] <- NA
CtoE[which(CtoE[,c(16)] == 'false'), c(16)] <- NA

CtoE.long <- CtoE %>% gather(topicality, answer, Answer.high.High:Answer.none.None, na.rm=T)
colnames(CtoE.long)
CtoE.long <- CtoE.long[, -c(14)] %>% gather(enumeration, answer, Answer.complete.complete:Answer.unrelated.Unrelated, na.rm = T)
CtoE.long <- CtoE.long[,-c(12)]

CtoE.long$topicality <- sapply(CtoE.long$topicality, function (x) substr(x, tail(gregexpr("\\.",x)[[1]],1)+1, nchar(x)))
CtoE.long$enumeration <- sapply(CtoE.long$enumeration, function (x) substr(x, tail(gregexpr("\\.",x)[[1]],1)+1, nchar(x)))

CtoE.long <- CtoE.long %>% group_by(HITId, Input.predE, Input.predC, Input.e_label, Input.c_label, 
                  Input.s_label, Input.o1_label, Input.o2_label) %>% summarise(time = mean(WorkTimeInSeconds), 
                                                                               high = sum(topicality == 'High'),
                                                                               moderate = sum(topicality == 'Moderate'),
                                                                               low = sum(topicality == 'Low'),
                                                                               none = sum(topicality == 'None'),
                                                                               complete = sum(enumeration == 'complete'),
                                                                               incomplete = sum(enumeration == 'incomplete'),
                                                                               unrelated = sum(enumeration == 'Unrelated')) 
CtoE.long$score = 0.5*(1/3)*(CtoE.long$high*1 + CtoE.long$moderate*(2/3) + CtoE.long$low*(1/3) + CtoE.long$none*0) +
                  0.5*(1/3)*(CtoE.long$complete*1 + CtoE.long$incomplete*0.5 + CtoE.long$unrelated*0)

EtoC <- read.csv(fname[index+3])
EtoC <- rbind(EtoC, read.csv(fname[index+4]))
EtoC <- rbind(EtoC, read.csv(fname[index+5]))
colnames(EtoC)
EtoC <- EtoC[,c(1,24,28:34,36,39,38,40,35,37,41)]
EtoC[which(EtoC[,c(10)] == 'false'), c(10)] <- NA
EtoC[which(EtoC[,c(11)] == 'false'), c(11)] <- NA
EtoC[which(EtoC[,c(12)] == 'false'), c(12)] <- NA
EtoC[which(EtoC[,c(13)] == 'false'), c(13)] <- NA
EtoC[which(EtoC[,c(14)] == 'false'), c(14)] <- NA
EtoC[which(EtoC[,c(15)] == 'false'), c(15)] <- NA
EtoC[which(EtoC[,c(16)] == 'false'), c(16)] <- NA

EtoC.long <- EtoC %>% gather(topicality, answer, Answer.high.High:Answer.none.None, na.rm=T)
colnames(EtoC.long)
EtoC.long <- EtoC.long[, -c(14)] %>% gather(enumeration, answer, Answer.complete.complete:Answer.unrelated.Unrelated, na.rm = T)
EtoC.long <- EtoC.long[,-c(12)]

EtoC.long$topicality <- sapply(EtoC.long$topicality, function (x) substr(x, tail(gregexpr("\\.",x)[[1]],1)+1, nchar(x)))
EtoC.long$enumeration <- sapply(EtoC.long$enumeration, function (x) substr(x, tail(gregexpr("\\.",x)[[1]],1)+1, nchar(x)))

EtoC.long <- EtoC.long %>% group_by(HITId, Input.predE, Input.predC, Input.e_label, Input.c_label, 
                        Input.s_label, Input.o1_label, Input.o2_label) %>% summarise(time = mean(WorkTimeInSeconds), 
                                                                                     high = sum(topicality == 'High'),
                                                                                     moderate = sum(topicality == 'Moderate'),
                                                                                     low = sum(topicality == 'Low'),
                                                                                     none = sum(topicality == 'None'),
                                                                                     complete = sum(enumeration == 'complete'),
                                                                                     incomplete = sum(enumeration == 'incomplete'),
                                                                                     unrelated = sum(enumeration == 'Unrelated')) 
EtoC.long$score = 0.5*(1/3)*(EtoC.long$high*1 + EtoC.long$moderate*(2/3) + EtoC.long$low*(1/3) + EtoC.long$none*0) +
    0.5*(1/3)*(EtoC.long$complete*1 + EtoC.long$incomplete*0.5 + EtoC.long$unrelated*0)
