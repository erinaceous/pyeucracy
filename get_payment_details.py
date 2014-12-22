#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    get_payment_details: 
        - Logs into ECOST
        - Fetches 'pending payments' page for a meeting
        - Fetches every pending payment, parses the page,
          can either output in JSON format (using the --json switch)
          or send all the details to the LaTeX compiler to fill in a
          template form with.

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
import os
import re


cost_prefix = 'https://e-services.cost.eu'
cost_login = 'user/login'
cost_payment_url_re = re.compile(
    cost_prefix.replace('/', '\/').replace(':', '\:').replace('.', '\.')\
    + '.*\/payments\/.*\/details\/'
)
cost_paymentid_re = re.compile(
    cost_prefix.replace('/', '\/').replace(':', '\:').replace('.', '\.')\
    + '.*\/payments\/(?P<paymentid>.*)\/details\/'
)
# print(cost_payment_url_re)


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


def parse_detail_page(content):
    soup = bs4.BeautifulSoup(content, 'html5lib')
    tags = soup.find_all('td')
    details = {}
    i = 0
    for tag in tags:
        if (i % 2) == 0:
            key = tag.get_text().strip()
        else:
            value = tag.prettify().replace('<br/>', '\n').replace('<td>', '')\
                    .replace('</td>', '')
            details[key] = value
        i += 1
    return details


defaults = {
    'formfrom': 'Dr Mark Neal',
    'formdepartment': 'Computer Science',
    'formdate': '\\today',
    'formbeneficiary': 'Name of Beneficiary',
    'formbankname': 'Name of Bank',
    'formaddress': 'The\\\\ Address\\\\ Of\\\\ The Person\\\\ And Stuff',
    'formbankaddress': 'The Country of Bank',
    'formcountry': 'The Country of Person',
    'formcurrency': 'EURO',
    'formtransfertype': 'Electronic Transfer',
    'formiban': 'LONGIBANCODEGOESHERE',
    'formswiftbic': '012345',
    'formamount': 'EURO $0000.00$',
    'formdetails': 'Longer detailed description of the payment.\\\\Spans multiple lines.\\\\Up to about\\\\Five\\\\of them.',
    'formoneproject': '11844',
    'formtotalproject': '11844',
    'formonecurrency': 'EURO',
    'formoneamount': '$0000.00$',
    'formoneaccount': '4006',
    'formoneproduct': 'TB002',
    'formonecurrency': 'EURO',
    'formoneamount': '$0000.00$',
    'formtotalcurrency': 'EURO',
    'formtotalamount': '$0000.00$'
}


def to_latex(details):
    keys = {
        'Reference': 'formdetails',
        'Amount EUR': 'formamount',
        'Bank Country': 'formbankaddress',
        'Beneficiary': 'formbeneficiary',
        'Bank Name': 'formbankname',
        'Account Holder': 'formaddress',
        'IBAN': 'formiban',
        'SWIFT': 'formswiftbic'
    }
    multi_newline = re.compile('\n+')
    # newline_at_start = re.compile('^')
    latexvars = dict(defaults)
    for key, val in keys.items():
        latexvars[val] = multi_newline.sub('\\\\', details[key].strip())\
                         .replace('\t', '').replace('\\ \\', '\\\\')
    latexvars['formcountry'] = latexvars['formaddress'].split('\\\\')[-1]
    latexvars['formaddress'] = '\\\\'.join(latexvars['formaddress'].split('\\\\')[:-1])
    latexvars['formtotalamount'] = latexvars['formamount'].replace('EUR ', '')
    latexvars['formoneamount'] = latexvars['formamount'].replace('EUR', '')
    return '\n'.join(['\\def\\%s{%s}' %
                      (key, val) for key, val in latexvars.items()])


def get_existing_files(path='./forms'):
    files = os.listdir(path)
    filename_re = re.compile('payment\.\d+\.[\w_-]+\.pdf$')
    for name in files:
        if filename_re.match(name):
            yield os.path.join(path, name)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', default=None)
    parser.add_argument('-p', '--password', default=None)
    parser.add_argument('-l', '--latex-prefix')
    parser.add_argument('-r', '--refresh', default=False, action='store_true')
    parser.add_argument('identifier')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.username is None:
        args.username = raw_input('Username: ')
    if args.password is None:
        args.password = getpass.getpass('Password: ')
    args.identifier = args.identifier.replace(cost_prefix, '')

    cj, request = login(args.username, args.password)
    
    # now we're logged in, fetch the pending payments
    request = get_authed_opener(cj)
    response = request.open(cost_prefix + '/' + args.identifier)
    content = response.read()
    # print(content)
    # print()

    # and extract the payment details URLs
    detail_urls = set(cost_payment_url_re.findall(content))
    current_files = list(get_existing_files())
    # print(detail_urls)

    utf8writer = codecs.getwriter('utf8')

    # and loop through each url
    for detail_url in detail_urls:
        url_match = cost_paymentid_re.match(detail_url)
        paymentid = 'null'
        if url_match is not None:
            paymentid = url_match.groupdict()['paymentid']
        request = get_authed_opener(cj)
        skip = False
        for name in current_files:
            if paymentid in name and not args.refresh:
                print('Skipping payment', paymentid, 'as file exists:', name)
                skip = True
                break
        if skip is True:
            continue
        print('Fetching payment ', paymentid, detail_url)
        response = request.open(detail_url)
        content = response.read()
        details = parse_detail_page(content)
        paymentname = details['Beneficiary'].strip().encode('ascii', 'ignore')\
                      .replace(' ', '_').lower()
        latex = to_latex(details)
        print(latex)
        print()
        vars_file = utf8writer(open(args.latex_prefix + '.temp.tex', 'w+'))
        print(latex, file=vars_file)
        vars_file.close()
        for i in range(0, 2):
            subprocess.call('pdflatex %s.overlay.tex' % args.latex_prefix,
                            shell=True)
        shutil.move('%s.overlay.pdf' % os.path.basename(args.latex_prefix),
                    'forms/payment.%s.%s.pdf' % (paymentid, paymentname))
        print()
        print()

    # save cookies
    cj.save(ignore_discard=True)
