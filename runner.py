'''
#=============================================================================
#     FileName: runner.py
#         Desc: 
#       Author: quake0day
#        Email: quake0day@gmail.com
#     HomePage: http://www.darlingtree.com
#      Version: 0.0.1
#   LastChange: 2011-08-23 15:42:47
#      History:
#=============================================================================
'''
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define,options
import os

# Tornado imports
import threading
import re
import simplejson as json

# Setup the queue
import Queue
tweetQueue = Queue.Queue(0)

#Define options that can be changed as we run this via the command line
define("port",default=8888,help="Run server on a specific port",type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        logging.info("Request to MainHandler!")
        #self.write("Great, now let's make this app speak in realtime")
        self.render("main.html")

class Tweet(object):
    waiters = [] # a list of clients waiting for updates
    cache = [] # a list of recent tweets
    cache_size = 200 # the amount of recent tweets to store

    def wait_for_messages(self,callback,cursor=None):
        cls = Tweet
        if cursor:
            index = 0
            for i in xrange(len(cls.cache)):
                index = len(cls.cache) - i - 1
                if cls.cache[index]["id"] == cursor:break
            recent = cls.cache[index +1:]
            if recent:
                callback(recent)
                return
        cls.waiters.append(callback)
    
    def new_tweets(self,messages):
        cls = Tweet
        for callback in cls.waiters:
            try:
                callback(messages)
            except:
                logging.error("Error in waiter callback",exc_info=True)
        cls.waiters = []
        cls.cache.extend(messages)
        if len(cls.cache) > self.cache_size:
            cls.cache = cls.cache[-self.cache_size:]

class UpdateHandler(tornado.web.RequestHandler,Tweet):
    @tornado.web.asynchronous
    def post(self):
        logging.info("Request to UpdateHandler!")
        cursor = self.get_argument("cursor",None)
        self.wait_for_messages(self.async_callback(self.on_new_tweets),cursor=cursor)

    def on_new_tweets(self,tweets):
        if not self.request.connection.stream.closed():
            self.finish(dict(tweets=tweets))

class TweetFirehose(threading.Thread):
    def run(self):
        import urllib2
        import base64
        import sys

        logging.info("Here!!")
        status_sample_url = 'http://stream.twitter.com/1/statuses/sample.json'
        request = urllib2.Request(status_sample_url)

        # Be sure to use your own twitter login information
        auth_basic = base64.encodestring('quake0day:13055301')[:-1]
        request.add_header('Authorization','Basic %s' % auth_basic)

        # open the connection 
        firehose = urllib2.urlopen(request)

        for tweet in firehose:
            if len(tweet) > 2:
                tweetQueue.put(tweet)

        firehose.close()

class TweetProcessor(threading.Thread):

    def run(self):
        import re
        import simplejson as json
        import uuid
        import sys

        # pre-compile some regular expressions
        links = re.compile("(http\:\/\/[^\ ]+)")
        hashtag = re.compile("(\#[0-9a-zA-Z]+)")
        ats = re.compile("(\@[0-9a-zA-Z]+)")
        retweets = re.compile("RT|via\ ")

        while True:
            tweet = tweetQueue.get()
            if tweet:
                t = json.loads(tweet)
                try:
                    stats = {}
                    stats['hashtags'] = hashtag.findall(t['text'])
                    stats['ats'] = ats.findall(t['text'])
                    stats['links'] = links.findall(t['text'])
                    stats['retweets'] = retweets.findall(t['text'])
                # pack the message up
                    message = {
                            "id":str(uuid.uuid4()),
                            "stats":stats
                            }
                    message["html"] = "<div class=\"message\" id=\"m"+\
                    message["id"] + "\"><strong>" + t['user']['screen_name'] + ":</strong>" + t['text'] + "</div>"
                    Tweet().new_tweets([message])
                except Exception,e:
                    pass

local_static_path = os.path.join(os.path.dirname(__file__),"static")

application = tornado.web.Application([
    (r"/",MainHandler),
    (r"/updates",UpdateHandler),
    ],static_path=local_static_path)

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    tornado.options.parse_command_line()

    myFirehose = TweetFirehose()
    myProcessor = TweetProcessor()
    myFirehose.start()
    myProcessor.start()
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

