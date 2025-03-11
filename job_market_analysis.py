import http.client
from flask import json, request, jsonify

conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "b61bbb41dfmsh6854e2ea484a585p12bd6ejsnd9aea51c469a",
    'x-rapidapi-host': "jsearch.p.rapidapi.com"
}

import urllib.parse

def fetch_salary_details(company, job_title):
    job_title_encoded = urllib.parse.quote(job_title)  # URL-encode the job title
    conn.request("GET", f"/company-job-salary?company={company}&job_title={job_title_encoded}&location_type=ANY&years_of_experience=ALL", headers=headers)
    
    res = conn.getresponse()
    data = res.read()
    
    return json.loads(data.decode("utf-8"))
