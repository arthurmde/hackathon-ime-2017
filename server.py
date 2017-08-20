from flask import Flask, redirect, render_template, request, session
import yaml
import json
import requests
from scopus.scopus_author import ScopusAuthor
import time
import scholarly

with open('config.yml') as f:
    config = yaml.load(f)

app = Flask(__name__)
app.debug = True


def search_profile(query):
    url = "https://api.mendeley.com/search/profiles"
    params = {'query': query,
              'limit': '20'  # default=20, max=100
              }
    headers = {'Accept': 'application/vnd.mendeley-profile.1+json',
               "Authorization": "Bearer " + config['accessToken']}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print('API ERROR:', response.status_code)
        return response.status_code
    return response.json()


def search_document(query, **kwargs):
    """
    You can use
        - min_year
        - max_year
    in kwargs to search
    papers in specific ranges
    """
    url = "https://api.mendeley.com/search/catalog"
    params = {'query': query,
              'limit': '100',  # default=20, max=100
              'view': 'stats'  # return the read counts
              }
    headers = {'Accept': 'application/vnd.mendeley-document.1+json',
               "Authorization": "Bearer " + config['accessToken']
               }
    if('min_year' in kwargs):
        params['min_year'] = kwargs['min_year']

    if('max_year' in kwargs):
        params['max_year'] = kwargs['max_year']

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print('API ERROR:', response.status_code)
        return response.status_code
    return response.json()


def get_document(document_id):
    url = "https://api.mendeley.com/search/catalog/" + document_id
    params = {'view': 'stats'  # return the read counts
              }
    headers = {'Accept': 'application/vnd.mendeley-document.1+json',
               "Authorization": "Bearer " + config['accessToken']
               }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print('API ERROR:', response.status_code)
        return response.status_code
    return response.json()


def get_profile(profile_id):
    url = "https://api.mendeley.com/search/profiles/" + profile_id
    headers = {'Accept': 'application/vnd.mendeley-document.1+json',
               "Authorization": "Bearer " + config['accessToken']
               }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print('API ERROR:', response.status_code)
        return response.status_code
    return response.json()


def colab_search(query, **kwargs):
    params = []  # params to pass to front-end
    publications = search_document(query, **kwargs)
    authors = {}
    for publication in publications:
        # There are buggy entries with thousands of authors, we do not want those
        if len(publication['authors']) >= 10:
            continue
        for author in publication['authors']:
            # Not all authors are real people (there are institutions)
            if 'scopus_author_id' not in author:
                continue
            scopus_id = author['scopus_author_id']
            if scopus_id not in authors:
                authors[scopus_id] = 0
            authors[scopus_id] += publication['reader_count']
    for scopus_id in sorted(authors, key=authors.get, reverse=True):
        author_params = {}
        if len(params) >= 10:
            break
        retries=3
        author_scopus_profile = None
        while retries:
            try:
                author_scopus_profile = ScopusAuthor(scopus_id)
                break
            except requests.exceptions.HTTPError:
                retries -= 1
        if author_scopus_profile == None:
            continue
        author_params['name'] = author_scopus_profile.name
        author_params['affiliation'] = author_scopus_profile._current_affiliation
        author_params['total_citations'] = author_scopus_profile.ncitations
        author_params['hindex'] = author_scopus_profile.hindex
        author_params['scopus_url'] = author_scopus_profile.scopus_url
        retries=3
        author_scholar_profile = None
        while retries:
            try:
                author_scholar_profile = next(scholarly.search_author("%s %s" % (author_scopus_profile.name, author_scopus_profile._current_affiliation.split(',')[0]))).fill()
                break
            except:
                retries -= 1
        if author_scholar_profile is None:
            continue
        author_params['scholar_url'] = 'https://scholar.google.com/citations?user=' + author_scholar_profile.id
        author_params['total_citations'] = author_scholar_profile.citedby
        author_params['interests'] = ', '.join(author_scholar_profile.interests)
        author_params['picture_url'] = 'https://scholar.google.com' + author_scholar_profile.url_picture
        author_params['hindex'] = author_scholar_profile.hindex
        author_params['i10index'] = author_scholar_profile.i10index
        params.append(author_params)
    return params


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/search')
def search():
    query = request.args.get('search')
    # params = colab_search(query)
    params = remove_me()
    return render_template('search.html', params=params)


def remove_me():
    return [{'name': 'Marisol García Valls', 'affiliation': 'Universidad Carlos III de Madrid, Department of Telematic Engineering', 'total_citations': 2280, 'hindex': 26, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=13806935900&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=wo4qj4UAAAAJ', 'interests': 'Computer Science, Distributed Real-Time Systems, Large scale and reliable systems', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=wo4qj4UAAAAJ&citpid=3', 'i10index': 59}]


if __name__ == '__main__':
    app.run()
