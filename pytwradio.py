#!/usr/bin/env python
# Copyright small2kuo 2014
# -*- coding: utf8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import argparse
import time
import urllib2
import re
import subprocess as sp
import socket
import time
from functools import wraps

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry

@retry(urllib2.URLError, tries=5, delay=0, backoff=0)
def urlopen_with_retry(req):
    return urllib2.urlopen(req)

class Pytwradio(object):
    """
    Capture Taiwan radio.
    """
    @classmethod
    def get_list(cls):
        urlobj = urlopen_with_retry('http://hichannel.hinet.net/ajax/radio/xml.do')
        content = urlobj.read()
        radiolist = re.findall('listname="([^\"]*)".*md_id="([^\"]*)"', content)
        radio_dict = {}
        for name, _id in radiolist:
            radio_dict[_id] = name.decode('utf8')
        return radio_dict

    def __init__(self, _id):
        self.id = str(_id)
        self.auth()
        self.radio_dict = self.get_list()
        self.base_url = ''
        self.auth_url = ''
        self.auth()

    @retry(urllib2.URLError, tries=5, delay=1, backoff=1)
    def auth(self):
        req = urllib2.Request(url='http://hichannel.hinet.net/player.do?id=%s&type=playradio' %self.id)
        req.add_header('Referer', 'http://hichannel.hinet.net/radio.do?id=%s' %self.id)
        urlobj = urlopen_with_retry(req)
        content = urlobj.read()
        urls = re.findall("http://radio-hichannel.cdn.hinet.net/live[^\"]*", content)
        if urls:
            url = urls[0]
            self.base_url = re.findall('.*/', url)[0]
            urlobj = urlopen_with_retry(url)
            content = urlobj.read()
            self.auth_url = self.base_url + content.split()[3]
        else:
            raise urllib2.URLError("ID not found or temporary error")


    def capture_nonblocking(self, t, output_file=None, DEBUG=False):
        fp = None
        if output_file: fp = open(output_file, "w")

        if DEBUG: print >>sys.stderr, "Caturing \"%s\": " % self.radio_dict[self.id]

        past_music_url = ''
        while t == -1 or t >= 0:
            ## Get data url
            try:
                urlobj = urlopen_with_retry(self.auth_url)
                content = urlobj.read()
                music_url = self.base_url + content.split('\n')[6]
            except Exception, e:
                print >>sys.stderr, e
                print self.auth_url
                self.auth()
                continue

            if music_url != past_music_url:
                # Capture data
                urlobj = urlopen_with_retry(music_url)
                buf = urlobj.read()

                # Output to screen/file/iterator
                if DEBUG: print >>sys.stderr, music_url
                if fp: fp.write(buf)
                yield buf

                if t != -1:
                    t -= 10
                    if t < 0: break
                past_music_url = music_url
            time.sleep(2)
        if fp: fp.close()

    def capture_blocking(self, t, output_file=None, DEBUG=False):
        data = ''
        for dat in self.capture_nonblocking(t, output_file, DEBUG): data += dat
        return data
    capture = capture_blocking


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steaming for Taiwan Radio")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-t", "--time", metavar='t', type=int, default=10, help='How long do you want to capture.')
    parser.add_argument("--id", help='See radio_id by --list')
    parser.add_argument("--list", action='store_true', help='show list of radio_id')
    parser.add_argument("--play", action='store_true', help='capture with playing radio')
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()

    if args.list or args.id is None:
        print 'id\tname'
        for key, value in sorted(Pytwradio.get_list().items(), key=lambda d: int(d[0])):
            print u'%s\t%s' %(key, value)
        exit()

    radio = Pytwradio(args.id)

    if args.play:
        pipe = sp.Popen(["ffplay","-"], stdin=sp.PIPE, stdout=sp.PIPE,  stderr=sp.PIPE, bufsize=0)
        t = 0
        for dat in radio.capture_nonblocking(t=args.time, output_file=args.output, DEBUG=True):
            pipe.stdin.write(dat)
        pipe.terminate()
    else:
        data = radio.capture(t=args.time, output_file=args.output, DEBUG=True)


