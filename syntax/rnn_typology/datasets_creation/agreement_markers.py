#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import suffixes

"""
An abstract class that adds agreement and case marks to sentence elements (verbs and their arguments).

Case system:

						SG			PL
	
	SUBJECT/ERGATIVE			~			^
	
	OBJECT/ABSOLUTIVE			#			*
	
	INDIRECT OBJECT / DATIVE		@			&
"""

class AgreementMarker(object):

	def __init__(self, add_cases):
	
		"""
		
		:param add_cases:
		
			a boolean. If true, adds case suffixes to NPs.
		"""
		
		self.add_cases = add_cases
		
	def mark(self, verb_node, agreement_nodes, add_gender = False, mark_auxiliary = True):
	
		cases = []
		is_transitive = any((n.label == "dobj" for n in agreement_nodes))
		verb_suffix = []
		
		for agreement_node in agreement_nodes:
		
			case = self.get_case(verb_node, agreement_node, is_transitive)
			gender = "" if not add_gender else agreement_node.gender
			
			verb_suffix.append((case, gender))

			if self.add_cases:
				
				cases.append((agreement_node, case))


		# verb_suffix = sorted(verb_suffix, key = lambda (case, gender): case)
		verb_suffix = sorted(verb_suffix, key = lambda x: x[0])
		verb_suffix = "".join([case + gender for (case, gender) in verb_suffix])
		found = False
		
		if mark_auxiliary:
			
			verb_children = verb_node.children
			auxiliaries = [c for c in verb_children if c.label == "aux" or c.label == "auxpass"]
			if len(auxiliaries) > 0:
				found = True
				last = auxiliaries[-1]
				cases.append((last, verb_suffix))
				
		if not found:
		
				cases.append((verb_node, verb_suffix))
		
		return cases
			
	def get_case(self, verb_node, agreement_node, is_transitive):
	
		raise NotImplementedError
		
		
class NominativeAccusativeMarker(AgreementMarker):

	def __init__(self, add_cases = False):
		super(NominativeAccusativeMarker, self).__init__(add_cases)
		
	def get_case(self, verb_node, agreement_node, is_transitive):

		#print "adding case to node ", agreement_node.word
		
		if agreement_node.label == "nsubj" or agreement_node.label == "nsubjpass":
				
			case = suffixes.nsubj_sg if agreement_node.number == "sg" else suffixes.nsubj_pl
					
		elif agreement_node.label == "dobj":
			
			case = suffixes.dobj_sg if agreement_node.number == "sg" else suffixes.dobj_pl
			
		elif agreement_node.label == "iobj":
			
				
			case = suffixes.iobj_sg if agreement_node.number == "sg" else suffixes.iobj_pl

		return case
		

class AmbigiousNominativeAccusativeMarker(AgreementMarker):

	def __init__(self, add_cases = False):
		super(AmbigiousNominativeAccusativeMarker, self).__init__(add_cases)
		
	def get_case(self, verb_node, agreement_node, is_transitive):

		#print "adding case to node ", agreement_node.word
		 
		if (agreement_node.label == "nsubj" or agreement_node.label == "nsubjpass"):
				
	
			case = suffixes.nsubj_sg if agreement_node.number == "sg" else suffixes.nsubj_pl
					
		elif agreement_node.label == "dobj":
			
			case = suffixes.dobj_sg if agreement_node.number == "sg" else suffixes.nsubj_sg
			
		elif agreement_node.label == "iobj":
			
				
			case = suffixes.iobj_sg if agreement_node.number == "sg" else suffixes.iobj_pl

		return case

		
class ErgativeAbsolutiveMarker(AgreementMarker):

	def __init__(self, add_cases=False):
		super(ErgativeAbsolutiveMarker, self).__init__(add_cases)
		
	def get_case(self, verb_node, agreement_node, is_transitive):

		is_subj = agreement_node.label == "nsubj" or agreement_node.label == "nsubjpass"
		
		if (not is_transitive and is_subj) or agreement_node.label == "dobj":
				
			case = suffixes.dobj_sg if agreement_node.number == "sg" else suffixes.dobj_pl
					
		elif is_transitive and is_subj:
			
			case = suffixes.nsubj_sg if agreement_node.number == "sg" else suffixes.nsubj_pl
			
		elif agreement_node.label == "iobj":
			
				
			case = suffixes.iobj_sg if agreement_node.number == "sg" else suffixes.iobj_pl
		
		return case
		
class AmbigiousErgativeAbsolutiveMarker(AgreementMarker):

	def __init__(self, add_cases=False):
		super(AmbigiousErgativeAbsolutiveMarker, self).__init__(add_cases)
		
	def get_case(self, verb_node, agreement_node, is_transitive):

		is_subj = agreement_node.label == "nsubj" or agreement_node.label == "nsubjpass"
		
		if (not is_transitive and is_subj) or agreement_node.label == "dobj":
				
			case = suffixes.dobj_sg if agreement_node.number == "sg" else suffixes.dobj_pl
					
		elif is_transitive and is_subj:
			
			case = suffixes.dobj_pl if agreement_node.number == "sg" else suffixes.nsubj_pl
			
		elif agreement_node.label == "iobj":
			
				
			case = suffixes.iobj_sg if agreement_node.number == "sg" else suffixes.iobj_pl
		
		return case

class ArgumentPresenceMarker(AgreementMarker):

	def __init__(self, add_cases=False):
		super(ArgumentPresenceMarker, self).__init__(add_cases)
		
	def get_case(self, verb_node, agreement_node, is_transitive):

		case = suffixes.dobj_sg if agreement_node.number == "sg" else suffixes.dobj_pl
		
		return case
		
