"""
main.py -- Udacity conference server-side Python App Engine
    HTTP controller handlers for memcache & task queue access

$Id$

created by wesc on 2014 may 24

"""

import webapp2
from google.appengine.api import app_identity
from google.appengine.api import mail
from connected import connectEDApi

class cleanPastEvents(webapp2.RequestHandler):
    def get(self):
        connectEDApi._eventsCleanPast()
        self.response.set_status(204)

class distributeEventHours(webapp2.RequestHandler):
    def get(self):
        connectEDApi._eventsDistributeRemainingHours()
        self.response.set_status(204)

class updateTopTeams(webapp2.RequestHandler):
    def get(self):
        connectEDApi._updateTopTeams()
        self.response.set_status(204)

app = webapp2.WSGIApplication([
    ('/crons/eventclean', cleanPastEvents),
    ('/crons/eventhours', distributeEventHours),
    ('/crons/topteams', updateTopTeams)
], debug=True)
