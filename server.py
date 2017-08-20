from flask import Flask, redirect, render_template, request, session
import yaml
import json
import requests
from scopus.scopus_author import ScopusAuthor
import time
import scholarly
import threading

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
        # usar 10 semafors, checar e pedir mais at'e termos 10
        if len(params) >= 10:
            break
        # THREADS
        def get_api_data(scopus_id):
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
        #end THREADS
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
    return [{'name': 'Danda B. Rawat', 'affiliation': 'Howard University, Department of Electrical Engineering and Computer Science', 'total_citations': 1415, 'hindex': 21, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=24725483600&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=Klr5kY4AAAAJ', 'interests': 'Cyber Security, Wireless Networks, Wireless Security, Internet of Things, Cloud Computing Security', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=Klr5kY4AAAAJ&citpid=20', 'i10index': 43}, {'name': 'Arjan Durresi', 'affiliation': 'Indiana University', 'total_citations': 3915, 'hindex': 30, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56271207400&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=MrVb9FkAAAAJ', 'interests': 'Network Architectures and Protocols, Security, Trust Management', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=MrVb9FkAAAAJ&citpid=3', 'i10index': 91}, {'name': 'Suleman Khan', 'affiliation': 'University of Malaya, Centre for Mobile Cloud Computing Research (C4MCCR)', 'total_citations': 269, 'hindex': 10, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56045629300&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=UMSsOboAAAAJ', 'interests': 'Software Defined Networks, Network Forensics, Network Security, Mobile Cloud Computing, IoT', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=UMSsOboAAAAJ&citpid=3', 'i10index': 10}, {'name': 'Abdullah Gani', 'affiliation': 'University of Malaya, Centre for Mobile Cloud Computing Research (C4MCCR)', 'total_citations': 4687, 'hindex': 34, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=7003355320&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=5iDbwdsAAAAJ', 'interests': 'Machine learning, wireless, networking, mobile cloud computing, Big Data', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=5iDbwdsAAAAJ&citpid=3', 'i10index': 99}, {'name': 'Ainuddin Wahid Abdul Wahab', 'affiliation': 'University of Malaya, Faculty of Computer Science and Information Technology', 'total_citations': 533, 'hindex': 12, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=55935556300&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=DY8bVx4AAAAJ', 'interests': 'Digital Forensics, Information Security, Information Hiding', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=DY8bVx4AAAAJ&citpid=3', 'i10index': 18}, {'name': 'Muhammad Khurram Khan', 'affiliation': 'King Saud University, Center of Excellence in Information Assurance', 'total_citations': 5144, 'hindex': 36, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=8942252200&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=99LlvYUAAAAJ', 'interests': 'Cybersecurity, Digital Authentication, Biometrics, Multimedia Security, Technological Innovation Management', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=99LlvYUAAAAJ&citpid=2', 'i10index': 129}, {'name': 'Juan Felipe Botero', 'affiliation': 'Universidad de Antioquia', 'total_citations': 1065, 'hindex': 12, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=35186051500&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=Ljd3pb0AAAAJ', 'interests': 'Network Virtualization, Virtual Network Embedding, Mathematical Programming, Future Internet', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=Ljd3pb0AAAAJ&citpid=2', 'i10index': 13}, {'name': 'Puneet Sharma', 'affiliation': 'Hewlett Packard Laboratories', 'total_citations': 12213, 'hindex': 43, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56856337800&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=gzzsQxAAAAAJ', 'interests': 'Computer Newtorks, SDN, NFV, Wireless, Mobility', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=gzzsQxAAAAAJ&citpid=2', 'i10index': 249}, {'name': 'Yongli Zhao', 'affiliation': 'Beijing University of Posts and Telecommunications, State Key Laboratory of Information Photonics and Optical Communications', 'total_citations': 1653, 'hindex': 20, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=56447285300&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=5v7basUAAAAJ', 'interests': 'Optical networking, SDN, Virtualization, 5G', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=5v7basUAAAAJ&citpid=2', 'i10index': 50}, {'name': 'Qi Qi', 'affiliation': 'Beijing University of Posts and Telecommunications, State Key Laboratory of Networking and Switching Technology', 'total_citations': 294, 'hindex': 8, 'scopus_url': 'https://www.scopus.com/authid/detail.uri?partnerID=HzOxMe3b&authorId=14058739100&origin=inward', 'scholar_url': 'https://scholar.google.com/citations?user=odjSydQAAAAJ', 'interests': 'Computer Vision, Texture Classification and Feature Design', 'picture_url': 'https://scholar.google.com/citations?view_op=view_photo&user=odjSydQAAAAJ&citpid=2', 'i10index': 6}]

if __name__ == '__main__':
    app.run()
