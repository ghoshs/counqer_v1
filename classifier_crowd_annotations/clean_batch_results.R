setwd('Documents/Thesis/counqer/classifier_crowd_annotations')
library(dplyr)

data <- read.csv('counting/Batch_3712921_batch_results.csv')

items <- data[, c(1, 28:41)]
items <- distinct(items)

merged <- data %>% group_by(HITId) %>% summarise(judgements = n(), yes = sum(Answer.yes.Yes == "true"),
                                                 maybe_yes = sum(Answer.maybe_yes.Maybe.yes == 'true'),
                                                 maybe_no = sum(Answer.maybe_no.Maybe.no == 'true'),
                                                 no = sum(Answer.no.No == 'true'),
                                                 do_not_know = sum(Answer.do_not_know.Do.not.know == 'true'))
merged <- inner_join(items, merged, by = "HITId")
write.csv(merged, 'counting/Batch_3712921_clean.csv', row.names = F)
