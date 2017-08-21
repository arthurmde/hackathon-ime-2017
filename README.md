# Colab Research

This project was developed during the [Hackathon USP
2017](https://hackathonusp2017.devpost.com/)

## Inspiration

We believe that collaboration is the key factor for impactful high-quality
research. CollabReSearch is a platform to support you in the hard task of
finding potential contributors to leverage your research and career!

## What it does

Collab Research is a search engine to help you find potential contributors to
leverage your research. The results are shown in a georeferenced map with 3
dimentions:

* Location - This can be seen in the map presented by the platform
* Relevance of the researcher publications in the area matched by the query
  string - This is represented by the **color** of the circle representing the
  researcher (Green > Yellow > Orange > Red)
* Productivity and citation impact of the researcher - Represented by the
  **size** of the circle representing the researcher (the bigger the circle,
  the higher his/her [hindex](https://en.wikipedia.org/wiki/H-index))

The user can click on the circles representing the researchers to get more
information about them, like

* hindex value
* Affiliation
* Total number of citations
* Areas of interest
* Links to Scopus and Google Scholar profiles
* Google Scholar profile picture

## How we built it

Since we did not have any access to CNPq's Lattes data (unfortunately the date
is not open for machines and require captchas to be accessed) we needed to use
3 different data sources to retrieve all the data needed to complete this
prototype:

* [Mendeley](https://www.mendeley.com)
* [Scopus](https://www.scopus.com)
* [Google Scholar](scholar.google.com)

First, we retrieve articles matching the queries entered by the user (relevance
provided by Mendeley). Then we retrieve all the authors of those articles and
give them points based on the number of views for the matching papers, also
provided by Mendeley. Finally, we query Scopus (API) and Google Scholar
(scrapper python lib) to retrieve more information about each researcher.

Since Scopus API is important to our process and it is quite slow, unstable,
and expensive, we decided to display at most 10 researchers in the map.

We used the Python programming language to fetch our data and provide a
back-end to our application using the [Flask](http://flask.pocoo.org/)
framework.

We used Google Maps API to plot our data and the Material Design Light library
to make our front-end.

## Accessing APIs

### Scopus

You need a scopus API token, then you should

* create the  `~/.scopus/my_scopus.py` file with

```
`MY_API_KEY='YOUR_KEY_HERE'
```

Note that this API does not provide free access. Chances are you can create a
token and access it from inside a University (we did it from Universidade de São Paulo)

### Mendeley

You will also need a Mendeley API

Your `config.yml` should look like

```
accessToken: YOUR_ACCESS_TOKEN
```

Note that Mendeley API expires every 1 hour. There is a way to auto-refresh it,
but we never got the time to implement such feature during the Hackathon.

## License

Copyright 2017 The AUTHORS

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

### AUTHORS

* Arthur Del Esposte
* Athos Ribeiro
* Lucas Kanashiro
