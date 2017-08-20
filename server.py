from flask import Flask, redirect, render_template, request, session
import yaml
import json
import requests
from scopus.scopus_author import ScopusAuthor
import scholarly
import threading
from sqlitedict import SqliteDict

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
    # THREADS
    def get_api_data(scopus_id, color_index):
        # check if there is stuff in DB
        cached = False
        author_params = author_in_db(scopus_id)
        if author_params is not None:
            cached = True
        else:
            author_params = {}
        author_scopus_profile = None
        author_params['scopus_id'] = scopus_id
        if color_index == 0:
            author_params['color'] = 'green'
        elif color_index >= 1 and color_index <= 3:
            author_params['color'] = 'yellow'
        elif color_index >= 4 and color_index <= 6:
            author_params['color'] = 'orange'
        else:
            author_params['color'] = 'red'
        if cached:
            params.append(author_params)
            return
        retries=3
        while retries:
            try:
                author_scopus_profile = ScopusAuthor(scopus_id)
                break
            except requests.exceptions.HTTPError:
                retries -= 1
        if author_scopus_profile is None:
            print('LOST DATA')
            return
        author_params['name'] = author_scopus_profile.name
        author_params['affiliation'] = author_scopus_profile._current_affiliation
        author_params['total_citations'] = author_scopus_profile.ncitations
        author_params['hindex'] = author_scopus_profile.hindex
        author_params['scopus_url'] = author_scopus_profile.scopus_url
        retries=2
        author_scholar_profile = None
        while retries:
            try:
                author_scholar_profile = next(scholarly.search_author("%s %s" % (author_scopus_profile.name, author_scopus_profile._current_affiliation.split(',')[0]))).fill()
                break
            except:
                retries -= 1
        if author_scholar_profile is None:
            params.append(author_params)
            print('LOST _GS_ DATA')
            return
        author_params['scholar_url'] = 'https://scholar.google.com/citations?user=' + author_scholar_profile.id
        author_params['total_citations'] = author_scholar_profile.citedby
        author_params['interests'] = ', '.join(author_scholar_profile.interests)
        author_params['picture_url'] = 'https://scholar.google.com' + author_scholar_profile.url_picture
        author_params['hindex'] = author_scholar_profile.hindex
        author_params['i10index'] = author_scholar_profile.i10index
        save_author_in_db(author_params)
        params.append(author_params)
    #end THREADS
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

    th_pool = []
    count = 0
    for scopus_id in sorted(authors, key=authors.get, reverse=True):
        # usar 10 semafors, checar e pedir mais at'e termos 10
        if count >= 10:
            break
        count += 1
        # Go for threads, yey!!!
        th = threading.Thread(target=get_api_data, args=[scopus_id, count])
        th_pool.append(th)
        th.start()
    for th in th_pool:
        th.join()
    return params


def author_in_db(scopus_id):
    my_dict = SqliteDict('./collab_research.sqlite')
    if scopus_id in my_dict:
        return my_dict[scopus_id]
    else:
        return None


def save_author_in_db(author_params):
    mydict = SqliteDict('./collab_research.sqlite')
    mydict[author_params['scopus_id']] = author_params
    mydict.commit()
    mydict.close()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/search')
def search():
    query = request.args.get('search')
    params = json.dumps(colab_search(query))
    #params = json.dumps(remove_me())
    return render_template('search.html', params=params)

# TODO: split no affiliation para localizAo
# TODO: move thread pool
# TODO: fix comma on queries

def remove_me():
    return [{'color': 'orange', 'name': 'Hlabishi I. Kobo', 'affiliation': 'Universiteit van Pretoria, Department of Electrical', 'total_citations': 1, 'hindex': 1, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=57193678823&origin=inward'}, {'color': 'red', 'name': 'Izzat Mahmoud Alsmadi', 'affiliation': 'Texas A and M University', 'total_citations': 230, 'hindex': 8, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=17433667400&origin=inward'}, {'color': 'red', 'name': 'Suleman Khan', 'affiliation': 'University of Malaya, Centre for Mobile Cloud Computing Research (C4MCCR)', 'total_citations': 269, 'hindex': 10, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56045629300&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=UMSsOboAAAAJ', 'interests': 'Software Defined Networks, Network Forensics, Network Security, Mobile Cloud Computing, IoT', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=UMSsOboAAAAJ&citpid=3', 'i10index': 10}, {'color': 'orange', 'name': 'Adnan M. Abu-Mahfouz', 'affiliation': 'The Council for Scientific and Industrial Research', 'total_citations': 148, 'hindex': 7, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=54419433200&origin=inward'}, {'color': 'red', 'name': 'Ahmed F. Aleroud', 'affiliation': 'Yarmouk University, Department of Computer Information Systems', 'total_citations': 45, 'hindex': 4, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=55053484000&origin=inward'}, {'color': 'red', 'name': 'Gerhard P. Hancke', 'affiliation': 'City University of Hong Kong', 'total_citations': 1538, 'hindex': 24, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=55647165548&origin=inward'}, {'color': 'yellow', 'name': 'Swetha Reddy Vamshidhar Reddy', 'affiliation': 'Georgia Southern University, Department of Electrical Engineering', 'total_citations': 13, 'hindex': 2, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=18635459300&origin=inward'}, {'color': 'yellow', 'name': 'Murat Karakus', 'affiliation': 'Indiana University-Purdue University Indianapolis, Department of Computer and Information Science', 'total_citations': 30, 'hindex': 3, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=54393351700&origin=inward'}, {'color': 'yellow', 'name': 'Danda B. Rawat', 'affiliation': 'Howard University, Department of Electrical Engineering and Computer Science', 'total_citations': 1415, 'hindex': 21, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=24725483600&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=Klr5kY4AAAAJ', 'interests': 'Cyber Security, Wireless Networks, Wireless Security, Internet of Things, Cloud Computing Security', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=Klr5kY4AAAAJ&citpid=20', 'i10index': 43}, {'color': 'orange', 'name': 'Arjan Durresi', 'affiliation': 'Indiana University', 'total_citations': 3915, 'hindex': 30, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56271207400&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=MrVb9FkAAAAJ', 'interests': 'Network Architectures and Protocols, Security, Trust Management', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=MrVb9FkAAAAJ&citpid=3', 'i10index': 91}]

if __name__ == '__main__':
    app.run()
