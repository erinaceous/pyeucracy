#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    get_payment_details: 
        - Logs into ECOST
        - Fetches contacts list for Action.
        - Outputs in CSV format.

    Original Author: Owain Jones [github.com/doomcat] [contact@odj.me]
"""

from __future__ import print_function
from cookielib import LWPCookieJar
import urllib, urllib2
import subprocess
import argparse
import html5lib
import getpass
import codecs
import pickle
import shutil
import bs4
import csv
import sys
import os
import re


cost_prefix = 'https://e-services.cost.eu'
cost_login = 'user/login'
cost_contacts_url = cost_prefix +\
    '/?module=aotools&action=contactsViewOther&aotoolsParam[actionId]={action_id}'


def login(username, password, cookiefile='cookies'):
    cj = LWPCookieJar(cookiefile)
    try:
        cj.load()
    except IOError:
        pass

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    formdata = {'sUsername': username, 'sPassword': password}
    data_encoded = urllib.urlencode(formdata)
    response = opener.open('/'.join([cost_prefix, cost_login]), data_encoded)
    content = response.read()
    # print(content)
    # print()
    cj.save(ignore_discard=True)
    return (cj, opener)


def get_authed_opener(cj):
    return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


def has_sorttag(tag):
    return tag.has_attr('sorttag')


def parse_detail_page(content):
    soup = bs4.BeautifulSoup(content, 'html5lib')
    # tags = soup.find_all('tr', class_=['odd_ecost', 'ev_ecost'])
    tags = soup.find_all(has_sorttag)
    return tags


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', default=None)
    parser.add_argument('-p', '--password', default=None)
    parser.add_argument('action_id')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.username is None:
        args.username = raw_input('Username: ')
    if args.password is None:
        args.password = getpass.getpass('Password: ')

    cj, request = login(args.username, args.password)
    
    # now we're logged in, fetch the pending payments
    request = get_authed_opener(cj)
    response = request.open(cost_contacts_url.format(action_id=args.action_id))
    content = response.read()
    tags = parse_detail_page(content)
    utf8writer = codecs.getwriter('utf8')
    utf8 = utf8writer(sys.stdout)

    print('\t'.join(['Title', 'First Name', 'Last Name', 'Category/Position',
                     'Institution', 'E-mail', 'Country']), file=utf8)
    for tag in tags:
        tds = tag.find_all('td')
        print('\t'.join([td.get_text().strip() for td in 
            tds[1], tds[2], tds[3], tds[4], tds[5], tds[6], tds[7]]),
            file=utf8)

    # save cookies
    cj.save(ignore_discard=True)
