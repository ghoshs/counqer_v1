setwd('/local/home/shrestha/Documents/Thesis/counqer/')

library(dplyr)
library(ggplot2)

### get predicate properties
data <- read.csv('pred_property_p_50/dbp_map.csv')
data <- rbind(data, read.csv('pred_property_p_50/dbp_raw.csv'))
data <- rbind(data, read.csv('pred_property_p_50/wd.csv'))
data <- rbind(data, read.csv('pred_property_p_50/fb.csv'))
data$predicate <- as.character(data$predicate)

### get predicate usage data
est_matches <- read.csv('predicate_usage_features/estimated_matches.csv')
est_matches[] <- lapply(est_matches, function(x) if (is.factor(x)) as.character(x) else {x})

data <- inner_join(data, est_matches, by='predicate')

### get predicate subject/object types
sub_obj_types <- read.csv('predicate_usage_features/sub_obj_types.csv')
sub_obj_types[] <- lapply(sub_obj_types, function(x) if (is.factor(x)) as.character(x) else {x})

data <- inner_join(data, sub_obj_types, by='predicate')

### get training labels
counting <- read.csv('classifier_crowd_annotations/counting/figure-eight/f1411878_grouped.csv')
counting[] <- lapply(counting, function(x) if (is.factor(x)) as.character(x) else {x})
enumerating <- read.csv('classifier_crowd_annotations/enumerating/figure-eight/f1413990_grouped.csv')
enumerating[] <- lapply(enumerating, function(x) if (is.factor(x)) as.character(x) else {x})

### finalize feature annotations
counting$final<- (counting$yes*1.0 + counting$maybe_yes*0.75 + 
                    counting$do_not_know*0.5 + counting$maybe_no*0.25 + counting$no*0)/counting$judgements
enumerating$final<- (enumerating$yes*1.0 + enumerating$maybe_yes*0.75 + 
                       enumerating$do_not_know*0.5 + enumerating$maybe_no*0.25 + enumerating$no*0)/enumerating$judgements

labelled_data_counting <- inner_join(data, counting[, c(1,9)], by='predicate')
labelled_data_enumerating <- inner_join(data, enumerating[, c(1,9)], by='predicate')


### write to dataset
write.csv(data, 'feature_file/predicates_p_50.csv', row.names = F)
write.csv(labelled_data_counting, 'feature_file/labelled_data_counting.csv', row.names = F)
write.csv(labelled_data_enumerating, 'feature_file/labelled_data_enumerating.csv', row.names = F)
