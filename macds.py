#!/usr/bin/python3

from urllib import request, parse
from http import cookiejar
from bs4 import BeautifulSoup
import re


class Schedule:
    """
    Represents a Weekly schedule with the weeks list containing each day.
    """
    def __init__(self, week=None):
        """
        :param week: list of days.
        """
        self.weeks = []
        if week:
            self.append_week(week)

    def append_week(self, week):
        """
        appends a week to the schedule
        :param week: list of days.
        """
        self.weeks.append(week)


def get_shift(username, password):
    """
    get_shift is the main point of entry for the module. It takes a username and password, and then encodes them
    in a url to be sent to the peoplestuff server. It then parses the returned html and converts it to a
    Schedule object representing the current week.
    """

    url = __create_url(username, password)
    resp = send_request(url)
    # list of shifts
    dl = parse_doc(resp)
    sch = Schedule(dl)
    return sch


def __create_url(username, password):
    """
    creates an url+encoded string with the passed username and password, plus some default values
    """
    base_url = "https://www.peoplestuffuk.com/WFMMCDPRD/LoginSubmit.jsp?"

    f = {'localCode': '', 'uType': '', 'switchUserID': '', 'browserTimeZoneOffset': '0',
         'txtUserID': username, 'txtPassword': password}
    u = base_url + parse.urlencode(f)
    return u


def send_request(url):
    """
    sendRequest creates a CookieJar and a Opener and then makes a http GET
    Request.

    :param url = url to open
    :type url = string
    """
    # the cookie jar is not used but the website will give a 500 error if you don't have one
    cj = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cj))

    resp = opener.open(url).read()
    return resp


def parse_doc(doc):
    """
    parseDoc uses Beautiful Soup to find the weeks from the dom string and then
    creates a list of tuples representing each day. The tuple is in the format ([day],[HH:MM-HH:MM])

    :param doc: html document
    :type doc: string
    :return list of tuples.
    """
    soup = BeautifulSoup(doc, "lxml")
    # find all input tags with an id that starts with "daydet"

    # loops through all input tags with an id beginning with 'daydet' and appends their value to a list
    d_list = []
    for val in soup.find_all('input', id=re.compile('^daydet')):
        s = val['value'].split(" : ", 1)
        d_list.append((s[0], s[1]))

    return d_list
