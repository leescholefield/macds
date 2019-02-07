#!/usr/bin/python3
# script to fetch shifts from the peoplestuff website.
# You will need a config python file with the username and password

from urllib import request, parse
from http import cookiejar
from datetime import datetime
from typing import List, Tuple
from lxml import etree
from lxml.html import HTMLParser
import config


class Schedule:
    """
    Represents a single week containing a list of shifts the user is working. Each entry in the list is a tuple of
    datetimes:  the first is the start of the shift, the second is the end.
    """
    def __init__(self, days_working: List[Tuple]):
        self.days_working = days_working


def get_schedule(username, password):
    """
    Sends an HTTP request to the peoplestuff server and then parses the result into a Schedule instance.

    :param username: username on the peoplestuff server
    :param password: password on the peoplestuff server
    :return: a new Schedule instance containing the users shifts for that week.
    """
    url = _create_url(username, password)
    resp = send_request(url)
    shifts = _parse_document(resp)

    return Schedule(shifts)


def _create_url(username, password):
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
    """
    # the cookie jar is not used but the website will give a 500 error if you don't have one
    cj = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cj))

    resp_body = opener.open(url).read()
    return resp_body


def _parse_document(doc) -> List[Tuple]:
    """
    Uses lxml to parse the HTML doc and pull out a list of the users shifts for that week.

    :return: a list with each entry a tuple containing a datetime for the start and end of each shift scheduled that
     week.
    """

    parser = HTMLParser()
    root = etree.fromstring(doc, parser=parser)

    day_list = []
    for val in root.xpath("//input[contains(@id, 'daydet')]/@value"):
        shift = _parse_shift_time(val)
        if shift:
            day_list.append(shift)

    return day_list


def _parse_shift_time(value):
    """
    Returns a tuple containing the start and end of the users shift as datetimes. Or none if the user does not have
    any shifts that day.
    """

    dt = value.split(" : ", 1)
    if len(dt) == 1:
        return None
    date = datetime.strptime(dt[0], '%A, %d/%m/%Y')

    tm = dt[1].split('-')
    if len(tm) == 1:
        return None

    start = datetime.strptime(tm[0], '%H:%M').time()
    start = datetime.combine(date, start)

    end = datetime.strptime(tm[1], '%H:%M').time()
    end = datetime.combine(date, end)

    return start, end

if __name__ == '__main__':
    s = get_schedule(config.username, config.password)
    for val in s.days_working:
        print('Day: {}, start: {}, end: {}'.format(str(val[0].date()), val[0].time(), val[1].time()))
