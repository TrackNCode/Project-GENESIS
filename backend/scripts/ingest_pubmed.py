import os
import json
import time
import requests
from typing import List, Dict

# NCBI requires a User-Agent and email for responsible usage
HEADERS = {
    "User-Agent": "ProjectGENESIS/0.1 (mailto:mvaibhav802@gmail.com)"
}
EMAIL = "mvaibhav802@gmail.com"

API_URL = os.getenv("GENESIS_API_URL", "http://127.0.0.1:8000")

def fetch_pubmed(query: str = "drug discovery", max_results: int = 5) -> List[Dict]:
    # Step 1: search for PMIDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    resp = requests.get(search_url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])

    # Step 2: fetch details for each PMID
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    docs = []
    for pmid in pmids:
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }
        r = requests.get(fetch_url, params=params, timeout=10)
        r.raise_for_status()
        # Very lightweight XML parse – extract Title and Abstract using simple string ops
        xml = r.text
        title_start = xml.find("<ArticleTitle>") + len("<ArticleTitle>")
        title_end = xml.find("</ArticleTitle>")
        title = xml[title_start:title_end] if title_start > -1 and title_end > -1 else ""
        abstract = ""
        if "<AbstractText>" in xml:
            abs_start = xml.find("<AbstractText>") + len("<AbstractText>")
            abs_end = xml.find("</AbstractText>")
            abstract = xml[abs_start:abs_end]
        text = f"{title}\n\n{abstract}".strip()
        docs.append({
            "id": pmid,
            "text": text,
            "metadata": {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
            },
        })
        time.sleep(0.2)  # be gentle on the API
    return docs

def ingest_documents(docs: List[Dict]):
    url = f"{API_URL}/knowledge/ingest"
    resp = requests.post(url, json=docs, timeout=15)
    resp.raise_for_status()
    print("Ingestion response:", resp.json())

if __name__ == "__main__":
    docs = fetch_pubmed()
    print(f"Fetched {len(docs)} documents, ingesting...")
    ingest_documents(docs)
