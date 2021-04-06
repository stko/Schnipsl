from whoosh.index import open_dir
#from whoosh.query import Every

ix = open_dir('indexdir')
#results = ix.searcher().search(Every('uri'))
all_docs = ix.searcher().documents()
for doc in all_docs:
	for f in doc.keys():
		print(f'index {f} : {doc[f]}')

