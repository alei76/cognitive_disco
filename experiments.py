import sys
import glob

import feature_functions as f
import label_functions as l

from naming_functions import doc_id_relation_id_nf
from feature_file_generator import generate_feature_files 
from prune_features import prune_features


def experiment0(mapping_file, dir_list):
	#ff_list = [f.bag_of_words]
	ff_list = [f.first3]
	dimension_mapper = l.GenericMapping(mapping_file)
	lf_list = dimension_mapper.get_all_label_functions()
	lf_list.append(l.OriginalLabel())
	nf = doc_id_relation_id_nf
	generate_feature_files(dir_list, ff_list, lf_list, nf, 'experiment0')

def experiment1(mapping_file, dir_list):
	brown_featurizer = f.BrownClusterFeaturizer()
	ff_list = [brown_featurizer.brown_word_pairs, f.production_rules]
	dimension_mapper = l.GenericMapping(mapping_file)
	lf_list = dimension_mapper.get_all_label_functions()
	lf_list.append(l.OriginalLabel())
	nf = doc_id_relation_id_nf
	generate_feature_files(dir_list, ff_list, lf_list, nf, 'experiment1')

def experiment1_1(mapping_file, dir_list):
	experiment_name = 'experiment1.1'
	ff_list = [f.production_rules]
	dimension_mapper = l.GenericMapping(mapping_file)
	lf_list = dimension_mapper.get_all_label_functions()
	lf_list.append(l.OriginalLabel())
	nf = doc_id_relation_id_nf
	generate_feature_files(dir_list, ff_list, lf_list, nf, experiment_name)
	prune_feature_files(dir_list[0], experiment_name, dimension_mapper.mapping_name, 5)


def experiment2(mapping_file, dir_list):
	experiment_name = 'experiment2'
	bf = f.BrownClusterFeaturizer()
	plf = f.LexiconBasedFeaturizer()
	ff_list = [
			f.is_arg1_multiple_sentences, 
			f.first_last_first_3, f.average_vp_length, f.modality, 
			plf.inquirer_tag_feature, 
			#plf.mpqa_score_feature, plf.levin_verbs, 
			f.production_rules, bf.brown_words, bf.brown_word_pairs]
	dimension_mapper = l.GenericMapping(mapping_file)
	lf_list = dimension_mapper.get_all_label_functions()
	lf_list.append(l.OriginalLabel())
	nf = doc_id_relation_id_nf
	generate_feature_files(dir_list, ff_list, lf_list, nf, experiment_name)

def experiment2_1(mapping_file, dir_list):
	experiment_name = 'experiment2.1'
	bf = f.BrownClusterFeaturizer()
	plf = f.LexiconBasedFeaturizer()
	ff_list = [
			f.is_arg1_multiple_sentences, 
			f.first_last_first_3, f.average_vp_length, f.modality, 
			plf.inquirer_tag_feature, 
			#plf.mpqa_score_feature, plf.levin_verbs, 
			f.production_rules, bf.brown_words, bf.brown_word_pairs]
	dimension_mapper = l.GenericMapping(mapping_file)
	lf_list = dimension_mapper.get_all_label_functions()
	lf_list.append(l.OriginalLabel())
	nf = doc_id_relation_id_nf
	generate_feature_files(dir_list, ff_list, lf_list, nf, experiment_name)
	prune_feature_files(dir_list[0], experiment_name, dimension_mapper.mapping_name, 5)

def prune_feature_files(training_dir, experiment_name, mapping_name, cutoff):
	file_patterns = '%s/%s.%s.*' % (training_dir, experiment_name, mapping_name)
	files = glob.glob(file_patterns)
	files.append('%s/%s.original_label.features' % (training_dir, experiment_name))
	print files
	for file_name in files:
		prune_features(file_name, cutoff)



def experiment_mapping_test(mapping_file, dir_list):
	ff_list = [f.bag_of_words]
	dimension_mapper = l.GenericMapping(mapping_file)
	nf = doc_id_relation_id_nf
	lf_list = dimension_mapper.get_all_label_functions()
	li_list.append(l.OriginalLabel())
	generate_feature_files(dir_list, ff_list, lf_list, nf, 'experiment_mapping_test')

def experiment_test(mapping_file, dir_list):
	ff_list = [f.production_rules]
	nf = doc_id_relation_id_nf
	lf_list = [] 
	lf_list.append(l.OriginalLabel())
	generate_feature_files(dir_list, ff_list, lf_list, nf, 'experiment_test')


if __name__ == '__main__':
	#execute the function named 'experiment_name'
	experiment_name = sys.argv[1]
	mapping_file = sys.argv[2]
	dir_list = sys.argv[3:]
	globals()[experiment_name](mapping_file, dir_list)


