"""Feature functions

Each function should take a data_reader.DRelation object as an argument,
and output a list of feature strings. 
If a function reuses some values from the object over and over,
the implementation should move to the methods not in the feature functions.

"""
import json
import os
import re
from nltk.tree import Tree


def first3(relation):
	feature_vector = []
	arg_tokens = relation.arg1_tokens
	arg_tokens.extend(relation.arg2_tokens)
	for arg_token in arg_tokens:
		feature = 'BOW_%s' % arg_token
		feature = re.sub(':','COLON', feature)
		feature_vector.append(feature)
	return feature_vector[0:3]

def bag_of_words(relation):
	"""Bag of words features

	: needs to be replaced with a string because 
	it will mess up Mallet feature vector converter
	"""
	feature_vector = []
	arg_tokens = relation.arg1_tokens
	arg_tokens.extend(relation.arg2_tokens)
	for arg_token in arg_tokens:
		feature = 'BOW_%s' % arg_token
		feature = re.sub(':','COLON', feature)
		feature_vector.append(feature)
	return feature_vector

def word_pairs(relation):
	"""Word pair features

	Bob is hungry. He wants a burger --> 
		Bob_He, Bob_wants, Bob_a, ... hungry_burger

	: needs to be replaced with a string because 
	it will mess up Mallet feature vector converter
	"""
	feature_vector = []
	for arg1_token in relation.arg1_tokens:
		for arg2_token in relation.arg2_tokens:
			feature = 'WP_%s_%s' % (arg1_token, arg2_token)
			feature = re.sub(':','COLON', feature)
			feature_vector.append(feature)
	return feature_vector

def _get_average_vp_length(parse_tree, arg_token_indices):
	if len(parse_tree.leaves()) == 0:
		return 0
	start_index = min(arg_token_indices)
	end_index = max(arg_token_indices) + 1
	if end_index - start_index == 1:
		return 0

	tree_position = parse_tree.treeposition_spanning_leaves(start_index, end_index)
	subtree = parse_tree[tree_position]

	agenda = [subtree]
	while len(agenda) > 0:
		current = agenda.pop(0)
		if current.height() > 2:
			if current.node == 'VP':
				return len(current.leaves())
			for child in current:
				agenda.append(child)
	return 0	

def average_vp_length(relation):
	arg1_tree, token_indices1 = relation.arg_tree(1)
	arg2_tree, token_indices2 = relation.arg_tree(2)
	arg1_average_vp_length = _get_average_vp_length(Tree(arg1_tree), token_indices1)
	arg2_average_vp_length = _get_average_vp_length(Tree(arg2_tree), token_indices2)
	if arg1_average_vp_length == 0 or arg2_average_vp_length == 0: 
		return []
	return ['ARG1_VP_LENGTH=%s' % arg1_average_vp_length,
			'ARG2_VP_LENGTH=%s' % arg2_average_vp_length,
			'VP_LENGTH_%s_%s' % (arg1_average_vp_length, arg2_average_vp_length)]

def _has_modality(words):
	for w in words:
		if w.pos == 'MD':
			return 'HAS_MODALITY'
	return 'NO_MODALITY'

def modality(relation):
	arg1_modality = _has_modality(relation.arg_words(1))
	arg2_modality = _has_modality(relation.arg_words(2))
	feature_vector = ['ARG1_%s' % arg1_modality,
			'ARG2_%s' % arg2_modality, 
			'ARG1_%s_ARG2_%s' % (arg1_modality, arg2_modality)]
	return feature_vector

def is_arg1_multiple_sentences(relation):
	arg1_sentence_indices = set([x.sentence_index for x in relation.arg_words(1)])
	if len(arg1_sentence_indices) > 1:
		return ['ARG1_MULTIPLE_SENTENCES'] 
	return []

def first_last_first_3(relation):
	"""First Last First 3 features 
	
	first and last of arg1
	first and last of arg2
	first of arg1 and arg2 together
	last of arg1 and arg2 together
	first three of arg1
	first three of arg2
	"""
	first_arg1 = relation.arg1_tokens[0]
	last_arg1 = relation.arg1_tokens[-1]
	first_arg2 = relation.arg1_tokens[0]
	last_arg2 = relation.arg1_tokens[-1]
	first_3_arg1 = '_'.join(relation.arg1_tokens[:3])
	first_3_arg2 = '_'.join(relation.arg2_tokens[:3])

	feature_vector = []
	feature_vector.append(first_arg1)
	feature_vector.append(last_arg1)
	feature_vector.append(first_arg2)
	feature_vector.append(last_arg2)
	feature_vector.append('FIRST_FIRST_%s__%s' % (first_arg1, first_arg2))
	feature_vector.append('LAST_LAST_%s__%s' % (last_arg1, last_arg2))
	feature_vector.append(first_3_arg1)
	feature_vector.append(first_3_arg2)
	return [re.sub(':','COLON',x) for x in feature_vector]

def production_rules(relation):
	arg1_tree, token_indices1 = relation.arg_tree(1)
	arg2_tree, token_indices2 = relation.arg_tree(2)
	rule_set1 = _get_production_rules(Tree(arg1_tree), token_indices1)
	rule_set2 = _get_production_rules(Tree(arg2_tree), token_indices2)
	
	if len(rule_set1) == 0 or len(rule_set2) == 0:
		return []

	#rule_set1_only = rule_set1 - rule_set2 
	#rule_set2_only = rule_set2 - rule_set1 
	rule_set1_only = rule_set1
	rule_set2_only = rule_set2

	feature_vector = []
	for rule in rule_set1.intersection(rule_set2):
		feature_vector.append('BOTH_ARGS_RULE=%s' % rule)
	for rule in rule_set1_only:
		feature_vector.append('ARG1RULE=%s' % rule)
	for rule in rule_set2_only:
		feature_vector.append('ARG2RULE=%s' % rule)
	return feature_vector
	
def _get_production_rules(parse_tree, token_indices):
	"""Find all of the production rules from the subtree that spans over the token indices

	Args:
		parse_tree : an nltk tree object that spans over the sentence that the arg is in
		token_indices : the indices where the arg is.

	Returns:
		a set of production rules used over the argument

	"""
	if len(parse_tree.leaves()) == 0:
		return set()
	if len(token_indices) == 1:
		tree_position = parse_tree.leaf_treeposition(token_indices[0])
		arg_subtree = parse_tree[tree_position[0:-1]]
	else:
		start_index = min(token_indices)
		end_index = max(token_indices) + 1
		tree_position = parse_tree.treeposition_spanning_leaves(start_index, end_index)
		arg_subtree = parse_tree[tree_position]

	rule_set = set()
	#try:
	for rule in arg_subtree.productions():
		s = rule.__str__()
		#we want to skip all of the unary production rules
		#if "'" not in s and 'ROOT' not in s:
		if 'ROOT' not in s:
			s = s.replace(' -> ', '->')
			s = s.replace(' ','_')
			s = s.replace(':','COLON')
			rule_set.add(s)
	#except:
		#print rule_set
		#pass
	return rule_set

class LexiconBasedFeaturizer(object):
	def __init__(self):
		home = os.path.expanduser('~')
		self.load_inquirer('%s/nlp/lib/lexicon/inquirer/inquirer_merged.json' % home)
		#self.load_mpqa('%s/nlp/lib/lexicon/mpqa_subj_05/mpqa_subj_05.json' % home)
		#self.load_levin('%s/nlp/lib/lexicon/levin/levin.json' % home)

	def load_inquirer(self, path):
		"""Load Inquirer General Tag corpus

		(WORD) --> [tag1, tag2, ...]
		"""
		try:
			lexicon_file = open(path)
			self.inquirer_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to load general inquirer corpus'

	def load_mpqa(self, path):
		"""Load MPQA dictionary
		
		(WORD) -->  [positive|negative, strong|weak]
		"""
		try:
			lexicon_file = open(path)
			self.mpqa_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to load mpqa corpus'

	def load_levin(self, path):
		"""Load Levin's verb class dictionary

		(WORD) --> [class1, class2, ...]
		"""
		try:
			lexicon_file = open(path)
			self.levin_dict = json.loads(lexicon_file.read())
		except:
			print 'fail to laod levin verb classes'

	def _get_inquirer_tags(self, words):
		tags = []
		for i, w in enumerate(words):
			key = w.word_token.upper()
			if key in self.inquirer_dict:
				tags.append(self.inquirer_dict[key])
		return tags
	
	def inquirer_tag_feature(self, relation):
		arg1_tags = self._get_inquirer_tags(relation.arg_words(1))
		arg2_tags = self._get_inquirer_tags(relation.arg_words(2))
		feature_vector = []
		if len(arg1_tags) > 0 and len(arg2_tags) > 0:
			for arg1_tag in arg1_tags:
				for arg2_tag in arg2_tags:
					feature_vector.append('TAGS=%s_%s' % (arg1_tag, arg2_tag))
		for arg1_tag in arg1_tags:
			feature_vector.append('ARG1_TAG=%s' % arg1_tag)
		for arg2_tag in arg1_tags:
			feature_vector.append('ARG2_TAG=%s' % arg1_tag)
		return feature_vector

	def mpqa_score_feature(self, relation):
		arg1_tree, token_indices1 = relation.arg_tree(1)
		arg2_tree, token_indices2 = relation.arg_tree(2)
		pass

	def levin_verbs(self, relation):
		arg1_tree, token_indices1 = relation.arg_tree(1)
		arg2_tree, token_indices2 = relation.arg_tree(2)
		pass


class BrownClusterFeaturizer(object):
	"""Brown Cluster-based featurizer

	We will only load the lexicon once and reuse it for all instances.
	Python goodness allows us to treat function as an object that is 
	still bound to another object

	lf = BrownClusterFeaturizer()
	lf.brown_pairs <--- this is a feature function that is bound to the lexicon

	"""
	def __init__(self):
		self.word_to_brown_mapping = {}
		brown_cluster_file_name  = 'brown-rcv1.clean.tokenized-CoNLL03.txt-c3200-freq1.txt'
		self._load_brown_clusters('resources/%s' % brown_cluster_file_name)

	def _load_brown_clusters(self, path):
		try:
			lexicon_file = open(path)
			for line in lexicon_file:
				cluster_assn, word, _ = line.split('\t')
				self.word_to_brown_mapping[word] = cluster_assn	
		except:
			print 'fail to load brown cluster data'

	def get_cluster_assignment(self, word):
		if word in self.word_to_brown_mapping:
			return self.word_to_brown_mapping[word]
		else:
			return 'UNK'

	def brown_words(self, relation):
		arg1_brown_words = set([self.get_cluster_assignment(x) for x in relation.arg1_tokens])
		arg2_brown_words = set([self.get_cluster_assignment(x) for x in relation.arg2_tokens])
		arg1_only = arg1_brown_words - arg2_brown_words
		arg2_only = arg2_brown_words - arg1_brown_words
		both_args = arg1_brown_words.intersection(arg2_brown_words)
		feature_vector = []
		for brown_word in both_args:
			feature_vector.append('BOTH_ARGS_BROWN=%s' % brown_word)
		for brown_word in arg1_only:
			feature_vector.append('ARG1_BROWN=%s' % brown_word)
		for brown_word in arg2_only:
			feature_vector.append('ARG2_BROWN=%s' % brown_word)
		return feature_vector

	def brown_word_pairs(self, relation):
		"""Brown cluster pair features
		
		From the shared task, this feature won NLP People's choice award.
		People like using them because they are so easy to implement and
		work decently well.

		"""
		feature_vector = []
		for arg1_token in relation.arg1_tokens:
			for arg2_token in relation.arg2_tokens:
				arg1_assn = self.get_cluster_assignment(arg1_token)
				arg2_assn = self.get_cluster_assignment(arg2_token)
				feature = 'BP_%s_%s' % (arg1_assn, arg2_assn)
				feature = re.sub(':','COLON', feature)
				feature_vector.append(feature)
		return feature_vector

