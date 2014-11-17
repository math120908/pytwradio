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

class Pytwradio:
    @classmethod
    def get_list(cls):
        content = urllib2.urlopen('http://hichannel.hinet.net/ajax/radio/xml.do').read()
        radiolist = re.findall('listname="([^\"]*)".*md_id="([^\"]*)"', content)
        radio_dict = {}
        for name, _id in radiolist:
            radio_dict[_id] = name.decode('utf8')
        return radio_dict
        

    def __init__(self, _id):
        self.id = str(_id)
        self.auth()
        self.radio_dict = self.get_list()

    def auth(self):
        req = urllib2.Request(url='http://hichannel.hinet.net/player.do?id=%s&type=playradio' %self.id)
        req.add_header('Referer', 'http://hichannel.hinet.net/radio.do?id=%s' %self.id)
        content = urllib2.urlopen(req).read()
        urls = re.findall("http://radio-hichannel.cdn.hinet.net/live[^\"]*",content)
        if urls :
            url = urls[0]
            self.base_url = re.findall('.*/',url)[0]
            self.auth_url = self.base_url + urllib2.urlopen(url).read().split()[3]
        else:
            raise Exception("ID not found.") 

    def capture(self, t, output_file=''):
        fp = None
        if output_file :
            fp = open(output_file,"w")
        print >>sys.stderr,"Caturing \"%s\": " % self.radio_dict[self.id],
        if not fp: print ''

        pass_music_url = ''
        while t==-1 or t >= 0 :
            try:
                music_url = self.base_url + urllib2.urlopen(self.auth_url).read().split('\n')[6]
            except Exception, e:
                print e
                self.auth()
                continue
            if music_url != pass_music_url:
                if fp:
                    fp.write(urllib2.urlopen(music_url).read())
                    sys.stdout.write('.')
                    sys.stdout.flush()
                else:
                    print music_url
                if t!=-1: 
                    t-=10
                    if t<0: break
                pass_music_url = music_url
            time.sleep(5)
        print ''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
        Steaming for Taiwan Radio
    """)
    parser.add_argument("-o", "--output", default = '')
    parser.add_argument("-t", "--time", metavar='t', type=int, default = 10, help='How long do you want to capture.')
    parser.add_argument("--id", help='See radio_id by --list')
    parser.add_argument("--list",action='store_true', help='show list of radio_id')
    args = parser.parse_args()

    if args.list or args.id==None:
        print 'id\tname'
        for key,value in sorted(Pytwradio.get_list().items(), key=lambda d:int(d[0])):
            print u'%s\t%s' %(key, value)
        exit()

    radio = Pytwradio(args.id)
    radio.capture(t=args.time, output_file=args.output)

