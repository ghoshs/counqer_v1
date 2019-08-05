setwd('/local/home/shrestha/Documents/Thesis/counqer/classifier_crowd_annotations')
library(dplyr)

############### Counting
results <- read.csv('counting/figure-eight/f1411878.csv')
results.minus.gold <- results[which(results$X_golden == "false"), -c(16:20)]

disabled_ids <- c(2393883419, 2398349110, 2393883423, 2393883422, 2393883421, 2393883420, 2393883418, 2393883417, 2393883416,
                  2393883415, 2393883411, 2393883410, 2393883409, 2393883408, 2393883407, 2393883405, 2393883404, 2393883403, 
                  2393883402, 2393883401, 2393883400, 2393883399, 2393883398)

results.minus.gold <- results.minus.gold[which(!(results.minus.gold$X_unit_id %in% disabled_ids)),]

results.grouped <- results.minus.gold %>% group_by(predicate, p_label) %>% 
                    summarise(judgements = n(),
                              yes = sum(does_the_relation_give_a_count_of_unique_entities == 'yes'),
                              maybe_yes = sum(does_the_relation_give_a_count_of_unique_entities == 'maybe_yes'),
                              maybe_no = sum(does_the_relation_give_a_count_of_unique_entities == 'maybe_no'),
                              no = sum(does_the_relation_give_a_count_of_unique_entities == 'no'),
                              do_not_know = sum(does_the_relation_give_a_count_of_unique_entities == 'do_not_know'))

fb_p_labels <- read.csv('counting/p_labels_fb.csv')
fb_p_labels[] <- lapply(fb_p_labels, function(x) if (is.factor(x)) as.character(x) else {x})

results.grouped[] <- lapply(results.grouped, function(x) if (is.factor(x)) as.character(x) else {x})
results.grouped$p_label[results.grouped$predicate %in% fb_p_labels$predicate] <- 
  inner_join(results.grouped[results.grouped$predicate %in% fb_p_labels$predicate,-c(2)], 
             fb_p_labels[fb_p_labels$predicate %in% results.grouped$predicate,], 
             by='predicate')$p_label

results.grouped$final <- ifelse((results.grouped$yes+results.grouped$maybe_yes > results.grouped$no+results.grouped$maybe_no),1,
                                ifelse((results.grouped$no+results.grouped$maybe_no > results.grouped$yes+results.grouped$maybe_yes),
                                       0,0.5))
write.csv(results.grouped, 'counting/figure-eight/f1411878_grouped.csv', row.names = F)

############### Enumerating
results <- read.csv('enumerating/figure-eight/f1413990.csv')
results.minus.gold <- results[which(results$X_golden == 'false'), ]

disabled_ids <- c(2401090584, 2401090602, 2401090608, 2401090611, 2401090613)
results.minus.gold <- results.minus.gold[which(!(results.minus.gold$X_unit_id %in% disabled_ids)),]

results.grouped <- results.minus.gold %>% group_by(predicate, p_label) %>% 
  summarise(judgements = n(),
            yes = sum(does_the_relation_enumerate_entities == 'yes'),
            maybe_yes = sum(does_the_relation_enumerate_entities == 'maybe_yes'),
            maybe_no = sum(does_the_relation_enumerate_entities == 'maybe_no'),
            no = sum(does_the_relation_enumerate_entities == 'no'),
            do_not_know = sum(does_the_relation_enumerate_entities == 'do_not_know'))
results.grouped$final <- ifelse((results.grouped$yes+results.grouped$maybe_yes > results.grouped$no+results.grouped$maybe_no),1,
                                ifelse((results.grouped$no+results.grouped$maybe_no > results.grouped$yes+results.grouped$maybe_yes),
                                       0,0.5))

write.csv(results.grouped, 'enumerating/figure-eight/f1413990_grouped.csv', row.names = F)
