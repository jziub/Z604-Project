#! /usr/bin/env python

"""
Extract features based on temporal language model.

Siyuan Guo, Apr 2014
"""

from pymongo import MongoClient
from collections import defaultdict
from math import log, log10
from utils import reshape
import pandas as pd


EPSILON = 0.00001
DATERANGES = ["pre-1839", "1840-1860", "1861-1876", "1877-1887", 
			  "1888-1895", "1896-1901", "1902-1906", "1907-1910", 
			  "1911-1914", "1915-1918", "1919-1922", "1923-present"]


class TLM(object):
	"""
	Temporal Language Model.

	Note, it's more like a bag-of-ngrams model than a true generative language 
	model. Each document and chronon is represented as a bag of ngrams.

	@param datec, connection to date collection in HTRC mongo database.
	@param tfc, connection to one of 'tf_1', 'tf_2' and 'tf_3' collections in 
		            HTRC mongo database.
	"""

	def __init__(self, datec, tfc):
		self.datec = datec
		self.tfc = tfc
		self.rtmatrix = pd.DataFrame()
		self.docids = []
		self.generate_rtmatrix()


	def get_rtmatrix(self):
		"""Getter for rtmatrix"""
		return self.rtmatrix


	def set_rtmatrix(self, rtmatrix):
		"""Setter for rtmatrix"""
		self.rtmatrix = rtmatrix


	def get_docids(self):
		"""Getter for docids"""
		return self.docids


	def set_docids(self, docids):
		"""Setter for docids"""
		self.docids = docids


	def generate_rtmatrix(self):
		"""
		Convert term frequencies stored in a MongoDB collection into a term*daterange 
		matrix. Each cell is raw frequency of a term occurring in a date range.
		(Unsmoothed)

		A sample daterange-term matrix output:
		             pre-1839      1840-1860 ...      1919-1922   1923-present  
		        273885.000000  257701.000000 ...  195615.000000  112005.000000  
		0         6532.000000    2463.000000 ...     845.000000    1052.000000  
		0"-03        0.000001       0.000001 ...       0.000001       0.000001    
		0"-04        0.000001       0.000001 ...       0.000001       0.000001
		...
		[281271 rows x 12 columns]
		"""

		# read all doc IDs for each date range from mongoDB into a dictionary:
		# {'pre-1839':['loc.ark+=13960=t9h42611g', ...], ...}
		dr_docid_dict = {}
		for daterange in DATERANGES:
			docs = self.datec.find({"range":daterange}, {"raw":0, "range":0})
			dr_docid_dict[daterange] = [doc['_id'] for doc in docs]

		# read term frquencies from mongoDB for each docid, then aggregate tf by 
		# timeslice, aggregated result is stored in a 2D dictionary:
		# {'pre-1839':{u'': 273885.0, u'1,808': 14.0, u'woode': 6.0, ...}, ...}
		dr_tf_dict = {}
		for daterange in DATERANGES:
			dr_tf_dict[daterange] = defaultdict(int)
			docids = dr_docid_dict[daterange]
			for docid in docids:
				tfdoc = self.tfc.find_one({"_id":docid})
				if tfdoc:
					# read raw term frequencies for each docid from mongoDB
					tfdict = tfdoc[u'freq']
					# merge & sum term frequencies for each date range
					for term in tfdict:
						dr_tf_dict[daterange][term] += tfdict[term]
				else:
					print "No term frequency for doc %s." % docid

		# Convert 2D dictionary into pandas dataframe (named matrix), with a simple
		rtmatrix = pd.DataFrame(dr_tf_dict).fillna(EPSILON)
		# Reorder columns of range * term matrix
		rtmatrix = rtmatrix[DATERANGES]
		self.set_rtmatrix(rtmatrix)
		self.set_docids(reduce(lambda x, y: x+y, dr_docid_dict.values()))



class NLLR(TLM):
	"""
	Temporal Entropy Weighted Normalized Log Likelihood Ratio 
	A document distance metric from Kanhabua & Norvag (2008)
	Lots of lambdas & idiomatic pandas functions will be used, they're superfast!

	@param datec, connection to date collection in HTRC mongo database.
	@param tfc, connection to one of 'tf_1', 'tf_2' and 'tf_3' collections in 
		            HTRC mongo database.
	@param nllrc, connection to one of 'nllr_1', 'nllr_2' and 'nllr_3' collections
					to store NLLR results.
	"""

	def __init__(self, datec, tfc, nllrc):
		TLM.__init__(self, datec, tfc)
		self.nllrc = nllrc


	@staticmethod
	def compute_llr(rtmatrix):
		"""
		Compute log( p(w|dr) / p(w/C) ), where dr is daterange and C is corpora.

		@param rtmatrix, a pandas dataframe representing term * daterange matrix.
		@return a 2D dictionary in format of {'pre-1839':{'term': 0.003, ...}, ...}
		"""
		# Normalize each column from freq to prob: p(w|dr)
		tfdaterange = rtmatrix.div(rtmatrix.sum(axis=0), axis=1)
		# Sum all columns into one column then convert from freq to prob: p(w|C)
		tfcorpora = rtmatrix.sum(axis=1)
		tfcorpora = tfcorpora.div(tfcorpora.sum(axis=0))
		# Compute log likelihood ratio
		llrmatrix = tfdaterange.div(tfcorpora, axis=0).applymap(log)
		return llrmatrix.to_dict()

		
	@staticmethod
	def compute_te(rtmatrix):
		"""
		Compute temporal entropy for each term.

		@param rtmatrix, a pandas dataframe representing term * daterange matrix.
		@return a dictionary of temporal entropies (term as key):
		        {u'murwara': 0.9999989777855017, 
		         u'fawn': 0.8813360127166802,
		         ... }
		"""
		# Normalize each row from freq to prob
		rtmatrix = rtmatrix.div(rtmatrix.sum(axis=1), axis=0)
		# compute temporal entropy and return it
		# note that our formula is a bit different from that in (N&K 2005)
		# instead of normalizing temporal entropy by 1/log(N), we simply use
		# 1/log(1500) because our number of documents in each chronon all 
		# around 1500.
		rtmatrix = rtmatrix.applymap(lambda x: x*log(x)).sum(axis=1)
		return rtmatrix.apply(lambda e: 1+1/log(1500)*e).to_dict()


	def compute_nllr(self, weighted=True):
		"""
		Compute normalized log likelihood ratio, using deJong/Rode/Hiemstra 
		Temporal Language Model, with a option of weighting by temporal 
		entropy.

		@param weighted, whether or not weighted by temporal entropy.
		@return a 2D dictionary of NLLRs in format {docid:{daterange: .. } .. }
		"""
		nllrdict = {}
		llrdict = self.compute_llr(self.get_rtmatrix())
		tedict = self.compute_te(self.get_rtmatrix()) if weighted else {}
		docids = self.get_docids()
		# read p(w|d) from MongoDB ('prob' field in tf_n collections)
		for docid in docids:
			tfdoc = self.tfc.find_one({u"_id":docid})
			if tfdoc:
				probs = tfdoc[u"prob"]
				nllrdict[docid] = {}
				for daterange in DATERANGES:
					nllrdict[docid][daterange] = sum([tedict[term] * probs[term] * llrdict[daterange][term] for term in probs])
		return nllrdict


	def run(self):
		"""Run"""
		nllrdict = self.compute_nllr()
		self.nllrc.insert(reshape(nllrdict))



class CS(TLM):
	"""
	Cosine similarity

	@param datec, connection to date collection in HTRC mongo database.
	@param tfc, connection to one of 'tf_1', 'tf_2' and 'tf_3' collections in 
		            HTRC mongo database.
	@param csc, connection to one of 'csc_1', 'csc_2' and 'csc_3' collections
					to store Cos-Sim results.
	"""
	
	def __init__(self, datec, tfc, csc):
		TLM.__init__(self, datec, tfc)
		self.csc = csc


	def compute_cs(self):
		"""
		Compute cosine similarity between each pair of term & chronon

		@return a 2D dictionary of CSs in format {docid:{daterange: .. } .. }
		"""



class KLD(TLM):
	"""
	Kullback-Leibler divergence

	@param datec, connection to date collection in HTRC mongo database.
	@param tfc, connection to one of 'tf_1', 'tf_2' and 'tf_3' collections in 
		            HTRC mongo database.
	@param kldc, connection to one of 'kld_1', 'kld_2' and 'kld_3' collections
					to store KL Divergence results.
	"""

	def __init__(self, datec, tfc, kldc):
		TLM.__init__(self, datec, tfc)
		self.kldc = kldc


	def compute_kld(self):
		"""
		Compute KL-Divergence for each pair of term & daterange

		@return a 2D dictionary of KLDs in format {docid:{daterange: .. } .. }
		"""
		klddict = {}
		docids = self.get_docids()
		rtmatrix = self.get_rtmatrix()
		# Normalize each column from freq to prob: p(w|dr)
		rtmatrix = rtmatrix.div(rtmatrix.sum(axis=0), axis=1).to_dict()
		for docid in docids:
			tfdoc = self.tfc.find_one({u"_id":docid})
			if tfdoc:
				probs = tfdoc[u"prob"]
				klddict[docid] = {}
				for daterange in DATERANGES:
					klddict[docid][daterange] = sum([probs[term] * log10(probs[term]/rtmatrix[daterange][term]) for term in probs])
		return klddict


	def run(self):
		"""Run"""
		klddict = self.compute_kld()
		self.kldc.insert(reshape(klddict))



class RunTLM(object):
	"""
	Run various computation based on TLM and save results to mongoDB.
	Collections 'date','tf_1','tf_2','tf_3','cf' must exist in mongoDB 
	before execution.

	@param outcollections, a list of names of output collections.
	"""

	def __init__(self, outcollections):
		db = self.connect_mongo(outcollections)
		self.datec = db.date
		self.tfcs = [db.tf_1, db.tf_2, db.tf_3]
		self.cfc = db.cf
		self.outcs = [db[outc] for outc in outcollections]


	@staticmethod
	def connect_mongo(outcollections):
		"""
		Connect to mongo, and check collection status.

		@param outcollections, a list of names of output collections.
		@return db connection.
		"""
		client = MongoClient('localhost', 27017)
		db = client.HTRC
		collections = db.collection_names()
		musthave = ['date', 'tf_1', 'tf_2', 'tf_3', 'cf']
		missing = set(musthave) - set(collections)
		if missing:
			raise IOError("Collections '%s' doesn't exist in 'HTRC' database. \
				Task aborted." % '&'.join(missing))
		for clc in outcollections:
			if clc in collections: 
				print "Collection %s already exists in 'HTRC' database. Drop it." % clc
				db.drop_collection(clc)
		return db


	def run_nllr(self):
		"""Run NLLR"""
		for outc, tfc in zip(self.outcs, self.tfcs):
			NLLR(self.datec, tfc, outc).run()


	def run_kld(self):
		"""Run KLD"""
		for outc, tfc in zip(self.outcs, self.tfcs):
			KLD(self.datec, tfc, outc).run()

	def run_ocr(self):
		"""Run OCR (NLLR based on character language model)"""
		NLLR(self.datec, self.cfc, self.outcs[0]).run()



if __name__ == '__main__':
	RunTLM(['nllr_1', 'nllr_2', 'nllr_3']).run_nllr()
	RunTLM(['kld_1', 'kld_2', 'kld_3']).run_kld()
	RunTLM(['nllr_ocr']).run_ocr()

