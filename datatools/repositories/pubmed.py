""" Pubmed repository functions """

from Bio import Entrez
from datetime import datetime
import pandas as pd

def esearch(db, query):
    handle = Entrez.esearch(db, term=query, retmax=100)
    record = Entrez.read(handle)
    handle.close()

    print(int(record["Count"]))

    return record

def esummary(db, id): 
    handle = Entrez.esummary(db=db, id=id)
    record = Entrez.read(handle)
    handle.close()
    return record

def pubmed_record(pubmed_summary): 
    pub_mapper = {
        'Id': 'study_pubmed_pubmed_id', 
        "Title":"study_pubmed_title", 
        "FullJournalName":"study_pubmed_journal", 
        "Issue":"study_pubmed_issue", 
        "Pages":"study_pubmed_pages", 
        'AuthorList':"study_pubmed_authors", 
    }

    study_pubmed = pd.DataFrame(pubmed_summary)
    study_pubmed = study_pubmed.rename(columns=pub_mapper)
    study_pubmed = study_pubmed.to_dict('records')[0]

    pub_date = datetime.strptime(study_pubmed['EPubDate'], "%Y %b %d")
    study_pubmed['study_pubmed_year'] = pub_date.year
    study_pubmed['study_pubmed_month'] = pub_date.month
    study_pubmed = study_pubmed | study_pubmed['ArticleIds']
    study_pubmed['study_pubmed_doi'] = study_pubmed.pop('doi', None)
    # # get field names for form
    form_name = 'study_pubmed'

    # r = redcap_worker.get_data({'content': 'metadata', 'forms[0]': form_name})
    # study_fields = [f['field_name'] for f in r]

    study_pubmed['study_pubmed_authors'] = ','.join(study_pubmed['study_pubmed_authors'])
    # study_pubmed = {k:v for k,v in study_pubmed.items() if k in study_fields}
    # study_pubmed['study_id'] = submission.record['study_id']

    return study_pubmed

def get_external_links(samples_df: pd.DataFrame, upload: bool = False): 
    pub_repo_links = samples_df.rename(columns={'Accession': 'public_repository_accession_id'})
    pub_repo_links = pub_repo_links.drop(columns=['Title'])
    pub_repo_links['public_repository_name'] = '7' # for GEO
    pub_repo_links = pub_repo_links.to_dict('records')
    return pub_repo_links

def get_abstract(pmid):
    handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
    abstract = handle.read()
    handle.close()
    return abstract