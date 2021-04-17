from whoosh.index import open_dir
#from whoosh.query import Every

sorted_data = {}

ix = open_dir('indexdir')
#results = ix.searcher().search(Every('uri'))
all_docs = ix.searcher().documents()
for doc in all_docs:
    sorted_data[doc['uri']] = doc
for sorted_uri in sorted(sorted_data.keys()):
    doc = sorted_data[sorted_uri]
    for f in doc.keys():
        print(f'index {f} : {doc[f]}')
    print('-------------')
