from flask import Flask, redirect, render_template, request, session
import yaml
import json
import requests

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
              'limit': '20',  # default=20, max=100
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
    publications = search_document(query, **kwargs)
    authors = {}
    print(len(publications))
    for publication in publications:
        # print(publication['title'])
        # print('numero de autores:', len(publication['authors']))
        # print('tipo:', publication['type'])
        # There are buggy entries with thousands of authors, we do not want those
        if len(publication['authors']) >= 10:
            continue
        for author in publication['authors']:
            if 'first_name' in author:
                # print(author['first_name'], author['last_name'])
                author_profile = search_profile('%s+%s' % (author['first_name'], author['last_name']))[0]
            else:
                # print('NO FIRST NAME', author['last_name'])
                author_profile = search_profile(author['last_name'])[0]
            print(author_profile['id'])
        # print()


@app.route('/')
def home():

    # return render_template('home.html', login_url=(auth.get_login_url()))
    return render_template('home.html')


@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/oauth')
def auth_return():

    return redirect('/listDocuments')


@app.route('/listDocuments')
def list_documents():

    name = 'foo'
    docs = 'bar'

    return render_template('library.html', name=name, docs=docs)


if __name__ == '__main__':
    app.run()
