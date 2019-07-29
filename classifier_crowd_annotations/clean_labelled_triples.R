setwd('Documents/Thesis/counqer')

fb_data <- read.csv('classifier_crowd_annotations/counting/counting_sample-fb-200.csv', sep='\t')
fb_data <- na.omit(fb_data)
set.seed(1)
fb_data <- fb_data[sample(nrow(fb_data), 100),]

data <- read.csv('classifier_crowd_annotations/counting/counting_sample.csv', sep='\t')
data <- data[1:300,]

data <- rbind(data, fb_data)
sum(is.na(data))
data[] <- lapply(data, function(x) if (is.factor(x)) as.character(x) else {x})

write.csv(data[, -c(4,7,10,13,16)], 'classifier_crowd_annotations/counting/counting_rows_figure_eight.csv', row.names = F)
    
samples[] <- lapply(samples, function(x) if (is.factor(x)) as.character(x) else {x})
tab_samples <- data.frame(subject=character(), relation=character(), object=integer())
for (i in 1:nrow(samples)) {
  p_idx = 11
  for (j in seq(1,10,2)){
    df = data.frame(subject=(samples[i,j]), relation=(samples[i,11]), object=(samples[i,j+1]))
    # print(df)
    tab_samples <- rbind(tab_samples, df) 
  }
}
write.csv(tab_samples, 'classifier_crowd_annotations/counting/counting_rows_ms_word.csv', row.names = F)