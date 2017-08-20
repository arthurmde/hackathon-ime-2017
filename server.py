from flask import Flask, redirect, render_template, request, session
import yaml
import json
import requests

with open('config.yml') as f:
    config = yaml.load(f)

app = Flask(__name__)
app.debug = True


def profile_search(query):
    url = "https://api.mendeley.com/search/profiles"
    params = {'query': query,
              'limit': '20'  # default=20, max=100
              }
    headers = {'Accept': 'application/vnd.mendeley-profile.1+json',
               "Authorization": "Bearer " + config['accessToken']}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return response.status_code
    return response.content


def catalog_search(query, **kwargs):
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
        return response.status_code
    return response.content


@app.route('/')
def home():

    # return render_template('home.html', login_url=(auth.get_login_url()))
    return render_template('home.html')


@app.route('/search')
def search():
    query = request.args('search')
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
