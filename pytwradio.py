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

class Pytwradio(object):
    """
    Capture Taiwan radio.
    """
    @classmethod
    def get_list(cls):
        urlobj = urllib2.urlopen('http://hichannel.hinet.net/ajax/radio/xml.do')
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

    def auth(self):
        req = urllib2.Request(url='http://hichannel.hinet.net/player.do?id=%s&type=playradio' %self.id)
        req.add_header('Referer', 'http://hichannel.hinet.net/radio.do?id=%s' %self.id)
        urlobj = urllib2.urlopen(req)
        content = urlobj.read()
        urls = re.findall("http://radio-hichannel.cdn.hinet.net/live[^\"]*", content)
        if urls:
            url = urls[0]
            self.base_url = re.findall('.*/', url)[0]
            urlobj = urllib2.urlopen(url)
            content = urlobj.read()
            self.auth_url = self.base_url + content.split()[3]
        else:
            raise Exception("ID not found.")

    def capture(self, t, output_file=None, DEBUG=False):
        fp = None
        if output_file:
            fp = open(output_file, "w")

        if DEBUG:
            print >>sys.stderr, "Caturing \"%s\": " % self.radio_dict[self.id]

        pass_music_url = ''
        data = '' 
        while t == -1 or t >= 0:
            try:
                urlobj = urllib2.urlopen(self.auth_url)
                content = urlobj.read()
                music_url = self.base_url + content.split('\n')[6]
            except Exception, e:
                print >>sys.stderr, e
                self.auth()
                continue
            if music_url != pass_music_url:
                urlobj = urllib2.urlopen(music_url)
                buf = urlobj.read()
                data += buf

                if fp:
                    fp.write(buf)
                if DEBUG:
                    print >>sys.stderr, music_url
                if t != -1:
                    t -= 10
                    if t < 0: break
                pass_music_url = music_url
            time.sleep(5)
        if fp: fp.close()
        return data 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steaming for Taiwan Radio")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-t", "--time", metavar='t', type=int, default=10, help='How long do you want to capture.')
    parser.add_argument("--id", help='See radio_id by --list')
    parser.add_argument("--list", action='store_true', help='show list of radio_id')
    parser.add_argument("--play", action='store_true', help='play after capture')
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

    data = radio.capture(t=args.time, output_file=args.output, DEBUG=True)

    if args.play:
        pipe = sp.Popen(["ffplay","-"], stdin=sp.PIPE, stdout=sp.PIPE,  stderr=sp.PIPE)
        pipe.stdin.write(data)
        pipe.terminate()

