#Project: connectED backend
#Created by: David Ramirez
#Date: 8/16/18
#Copyright 2018 LeapWithAlice,LLC. All rights reserved

import httplib
import endpoints
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import ndb

SKILLS_LIST = [ 'academics',
    'administrative',
    'advocacy',
    'bilingual',
    'business management',
    'clerical',
    'coaching',
    'communications',
    'computers',
    'design & graphic arts',
    'electrical',
    'finance',
    'fund raising',
    'engineering',
    'food services',
    'event management',
    'health care',
    'hobbies and crafts',
    'human resources',
    'IT infrastructure',
    'landscaping',
    'legal',
    'logistics',
    'marketing',
    'music',
    'non-profit development',
    'performing arts',
    'plumbing',
    'strategic planning',
    'social services',
    'software development',
    'trades',
    'tutor',
    'web development']

INTERESTS_LIST = ['Advocacy and Human Rights', 
    'Animals', 
    'Arts & culture', 
    'Children & Youth', 
    'Community', 
    'Counseling', 
    'Crisis Support', 
    'Disaster Relief', 
    'Education & Literacy', 
    'Emergency & Safety'
    'Employment',
    'Environment',
    'Faith-based',
    'Health & Medicine',
    'Homeless & Housing',
    'Human Services',
    'Hunger',
    'Immigrants & Refugees',
    'international',
    'Justice & Legal',
    'LGBTQ',   
    'Media',
    'Mentoring',
    'People with Disabilities',
    'Politics',
    'Seniors',
    'Sports & Recreation',
    'Technology',
    'Veterans',
    'Women']

EDUCATION_LIST = ['Completed 8th grade',
    'Some high school',
    'HS diploma',
    'Some college',
    'Associates degree',
    'Bachelors degree',
    'Masters degree',
    'Doctoral degree']

COMPLAINT_LIST = ['placeholder','placeholder2']







#Resource container models are used to get url query strings from HTTP requests sent to the API



##################################################################################
##################         PROTORPC MESSAGE MODELS          ######################
##################################################################################

#Team related messages------------------------------------------------------------
class TeamCreateForm(messages.Message):
    t_name = messages.StringField(1, required=True)
    t_desc = messages.StringField(2)
    t_photo = messages.StringField(3)
    #t_capacity = messages.IntegerField(4)
    t_privacy = messages.StringField(4)

class TeamGetResponse(messages.Message):
    t_name = messages.StringField(1)
    t_orig_name = messages.StringField(2)
    t_desc = messages.StringField(3)
    t_photo = messages.StringField(4)
    #t_capacity = messages.IntegerField(5)
    t_organizer = messages.StringField(5)
    t_members = messages.IntegerField(6)
    t_privacy = messages.StringField(7)
    funds_raised = messages.IntegerField(8)
    t_pending_members = messages.IntegerField(9)

class TeamRosterGetResponse(messages.Message):
    leaders = messages.StringField(1, repeated=True)
    members = messages.StringField(2, repeated=True)
    pending_members = messages.StringField(3, repeated=True)


class TeamEditForm(messages.Message):
    t_name = messages.StringField(1)
    t_orig_name = messages.StringField(2, required=True)
    t_desc = messages.StringField(3)
    t_photo = messages.StringField(4)
    #t_capacity = messages.IntegerField(5)
    t_privacy = messages.StringField(5)


#Profile related messages------------------------------------------------------------
class ProfileCreateForm(messages.Message):
    first_name = messages.StringField(1, required=True)
    last_name = messages.StringField(2, required=True)
    lat = messages.FloatField(3, required=True)
    lon = messages.FloatField(4, required=True)
    interests = messages.StringField(5, repeated=True)
    education = messages.StringField(6, required=True)
    skills = messages.StringField(7, repeated=True)
    mon = messages.BooleanField(8, default=True)
    tue = messages.BooleanField(9, default=True)
    wed = messages.BooleanField(10, default=True)
    thu = messages.BooleanField(11, default=True)
    fri = messages.BooleanField(12, default=True)
    sat = messages.BooleanField(13, default=True)
    sun = messages.BooleanField(14, default=True)
    time_day = messages.StringField(15)
    photo = messages.StringField(16)

class ProfileGetResponse(messages.Message):
    first_name = messages.StringField(1, required=True)
    last_name = messages.StringField(2, required=True)
    lat = messages.FloatField(3, required=True)
    lon = messages.FloatField(4, required=True)
    interests = messages.StringField(5, repeated=True)
    education = messages.StringField(6, required=True)
    skills = messages.StringField(7, repeated=True)
    photo = messages.StringField(8)

class GetProfileEvents(messages.Message):
    registered_events = messages.StringField(1, repeated=True)
    completed_events = messages.StringField(2, repeated=True)
    created_events = messages.StringField(3, repeated=True)

class ProfileEditForm(messages.Message):
    first_name = messages.StringField(1)
    last_name = messages.StringField(2)
    lat = messages.FloatField(3)
    lon = messages.FloatField(4)
    interests = messages.StringField(5, repeated=True)
    education = messages.StringField(6)
    skills = messages.StringField(7, repeated=True)
    mon = messages.BooleanField(8)
    tue = messages.BooleanField(9)
    wed = messages.BooleanField(10)
    thu = messages.BooleanField(11)
    fri = messages.BooleanField(12)
    sat = messages.BooleanField(13)
    sun = messages.BooleanField(14)
    time_day = messages.StringField(15)
    photo = messages.StringField(16)
    new_password = messages.StringField(17)

class EmailResponse(messages.Message):
    email = messages.StringField(1, required=True)

#Event related messages------------------------------------------------------------
class EventCreateForm(messages.Message): 
    e_title = messages.StringField(1, required=True)
    e_desc = messages.StringField(2)
    e_photo = messages.StringField(3)
    #e_lat = messages.FloatField(6, required=True)
    #e_lon = messages.FloatField(7, required=True)
    capacity = messages.IntegerField(4)
    street = messages.StringField(5,required=True)
    city = messages.StringField(6,required=True)
    state = messages.StringField(7,required=True)
    zip_code = messages.StringField(8, required=True)
    env = messages.StringField(9,required=True)
    req_skills = messages.StringField(10,repeated=True)
    interests = messages.StringField(11,repeated=True)
    education= messages.StringField(12)
    privacy = messages.StringField(13)
    qr = messages.StringField(14)
    date = messages.StringField(15, repeated=True)
    day = messages.StringField(16, repeated=True)
    start = messages.StringField(17, repeated=True)
    end = messages.StringField(18, repeated=True)

class EventGetResponse(messages.Message): 
    e_orig_title = messages.StringField(1)
    e_title = messages.StringField(2)
    e_organizer = messages.StringField(3)
    e_desc = messages.StringField(4)
    e_photo = messages.StringField(5)
    e_lat = messages.FloatField(6)
    e_lon = messages.FloatField(7)
    capacity = messages.IntegerField(8)
    street = messages.StringField(9)
    city = messages.StringField(10)
    state = messages.StringField(11)
    zip_code = messages.StringField(12)
    env = messages.StringField(13)
    req_skills = messages.StringField(14,repeated=True)
    interests = messages.StringField(15,repeated=True)
    education= messages.StringField(16)
    privacy = messages.StringField(17)
    qr = messages.StringField(18)
    date = messages.StringField(19, repeated=True)
    day = messages.StringField(20, repeated=True)
    start = messages.StringField(21, repeated=True)
    end = messages.StringField(22, repeated=True)
    num_attendees = messages.IntegerField(23)
    funds_raised = messages.IntegerField(24)
    num_pending_attendees = messages.IntegerField(25)

class EventRosterGetResponse(messages.Message):
    teams = messages.StringField(1, repeated=True)
    attendees = messages.StringField(2, repeated=True)
    pending_attendees = messages.StringField(3, repeated=True)
    signed_in_attendees = messages.StringField(4, repeated=True)
    signed_out_attendees = messages.StringField(5, repeated=True)
    leaders = messages.StringField(6, repeated=True)
    organizer = messages.StringField(7)

class EventUpdatesGetResponse(messages.Message):
    updates = messages.StringField(1, repeated=True)
    u_datetime = messages.StringField(2, repeated=True)


class EventEditForm(messages.Message): 
    #e_organizer and e_orig_title are non-modifiable properties that must be included to identify the Event entity in Datastore
    e_orig_title = messages.StringField(1, required=True)

    e_title = messages.StringField(2)
    e_desc = messages.StringField(3)
    e_photo = messages.StringField(4)
    e_lat = messages.FloatField(5)
    e_lon = messages.FloatField(6)
    capacity = messages.IntegerField(7)
    street = messages.StringField(8)
    city = messages.StringField(9)
    state = messages.StringField(10)
    zip_code = messages.StringField(11)
    env = messages.StringField(12)
    req_skills = messages.StringField(13)
    interests = messages.StringField(14)
    education= messages.StringField(15)
    privacy = messages.StringField(16)
    qr = messages.StringField(17)
    #all the following array indices must match up
    date = messages.StringField(18, repeated=True)
    day = messages.StringField(19, repeated=True)
    start = messages.StringField(20, repeated=True)
    end = messages.StringField(21, repeated=True)
    search_rad = messages.IntegerField(22)


class EventNameResponse(messages.Message): 
    event_name = messages.StringField(1)

class EventAddLeaders(messages.Message): 
    #e_organizer and e_orig_title are non-modifiable properties that must be included to identify the Event entity in Datastore
    leaders = messages.StringField(1, repeated=True)

class addEventLeadersResponse(messages.Message):
    leaders = messages.StringField(1, repeated=True)

class GetEventsInRadiusResponse(messages.Message):
    events = messages.StringField(1, repeated=True)
    distances = messages.FloatField(2, repeated=True)

class GetEventsInRadiusByDateResponse(messages.Message):
    events = messages.StringField(1, repeated=True)

class EventSearchResponse(messages.Message):
    event_titles = messages.StringField(1, repeated=True)
    event_ids = messages.StringField(2, repeated=True)
    distances = messages.FloatField(3, repeated=True)

class EventApproveRequest(messages.Message):
    approve_list = messages.StringField(1, repeated=True)

class TeamApproveRequest(messages.Message):
    approve_list = messages.StringField(1, repeated=True)

class TeamRequest(messages.Message):
    team = messages.StringField(1)

class EmptyResponse(messages.Message):
    nothing = messages.IntegerField(1)




##################################################################################
###############      RESOURCE CONTAINER (REQUESTS) MODELS         ################
##################################################################################

#empty Resource container 
EMPTY_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage
)

#Resource container for deleting profile (gets email)
PROF_DEL_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage
)

#source container for getting profile (gets email)
PROF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    email_to_get=messages.StringField(1, required=True)
)

#Resource container for deleting profile (gets email)
EVENT_DEL_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    e_organizer_email=messages.StringField(1),
    url_event_orig_name=messages.StringField(2, required=True)
)

#Resource container for approving pending event attendees (gets email)
EVENT_APPROVE_REQUEST = endpoints.ResourceContainer(
    EventApproveRequest,
    e_organizer_email=messages.StringField(1),
    url_event_orig_name=messages.StringField(2, required=True), 
)

#Resource container for adding leaders to event (needed for url)
EVENT_ADD_LEADERS_REQUEST = endpoints.ResourceContainer(
    EventAddLeaders,
    url_event_orig_name=messages.StringField(1, required=True)
)

#Resource container for adding leaders to event (needed for url)
EVENT_DELETE_LEADERS_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    url_event_orig_name=messages.StringField(1, required=True),
    leaders=messages.StringField(2, repeated=True)
)

#Resource container for deleting team (needed for url)
TEAM_DEL_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    url_team_orig_name=messages.StringField(3, required=True)
)

EVENT_SEARCH_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    search_term = messages.StringField(1, required = True)
)
"""
TEAM_EVENT_REG_REQUEST = endpoints.ResourceContainer(
    TeamEventRegRequest,
    e_organizer_email = messages.StringField(1, required=True),
    url_event_orig_name = messages.StringField(2, required=True),
)

TEAM_EVENT_DEREG_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    e_organizer_email = messages.StringField(1, required=True),
    url_event_orig_name = messages.StringField(2, required=True),
    team = messages.StringField(3, required=True)
)
"""
APPROVE_TEAM_MEMBERS_REQUEST  = endpoints.ResourceContainer(
    TeamApproveRequest,
    team_name = messages.StringField(1, required=True)
)

"""
APPROVE_PENDING_TEAMS_REQUEST  = endpoints.ResourceContainer(
    TeamApproveRequest,
    e_organizer_email = messages.StringField(1, required=True),
    url_event_orig_name = messages.StringField(2, required=True)
)
"""

QR_SIGNIN_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    e_organizer_email=messages.StringField(1, required=True),
    url_event_orig_name=messages.StringField(2, required=True)
)

REGISTER_EVENT_REQUEST = endpoints.ResourceContainer(
    TeamRequest,
    e_organizer_email=messages.StringField(1, required=True),
    url_event_orig_name=messages.StringField(2, required=True)
)
##################################################################################
##################           DATASTORE MODELS               ######################
##################################################################################

#Profile related models------------------------------------------------------------
class Report(ndb.Model):
    '''Report -- Report object (nested in Profile object)'''
    r_type = ndb.StringProperty(required=True)
    r_desc = ndb.TextProperty()
    r_date = ndb.DateProperty (required=True)
    sender = ndb.StringProperty (required=True)

class Profile(ndb.Model):
    '''Profile -- Profile object'''
    email = ndb.StringProperty(required=True)
    first_name = ndb.StringProperty(required=True)
    last_name = ndb.StringProperty(required=True)
    location = ndb.GeoPtProperty()
    interests = ndb.StringProperty(repeated=True)
    education = ndb.StringProperty()
    skills = ndb.StringProperty(repeated=True)
    #list of events user is attending or has attended
    #events = ndb.StringProperty(repeated=True)
    #hours of activity accumulated
    hours = ndb.FloatProperty(default=None)
    funds_raised = ndb.IntegerProperty(default=None)
    reports = ndb.StructuredProperty(Report, repeated=True)
    attended_events = ndb.StringProperty(repeated=True)
    completed_events = ndb.StringProperty(repeated=True)
    event_hours = ndb.FloatProperty(repeated=True)
    #list of created events
    created_events = ndb.StringProperty(repeated=True)
    #list of events user is leader of
    #events_leader = ndb.StringProperty(repeated=True)
    #pending_events = ndb.StringProperty(repeated=True)
    #list of teams user is part of 
    #teams = ndb.StringProperty(repeated=True)
    #list of teams user is organizer of
    created_teams = ndb.StringProperty(repeated=True)
    #ist of teams user is leader of 
    #teams_leader = ndb.StringProperty(repeated=True)
    #pending_teams = ndb.StringProperty(repeated=True)
    photo = ndb.TextProperty()
    search_rad = ndb.IntegerProperty(default=100)
    qr_in_dt = ndb.DateTimeProperty()


class Sched(ndb.Model):
    '''DT_Pref -- DT_Pref object (child of Profile object'''
    mon = ndb.BooleanProperty(default=True)
    tue = ndb.BooleanProperty(default=True)
    wed = ndb.BooleanProperty(default=True)
    thu = ndb.BooleanProperty(default=True)
    fri = ndb.BooleanProperty(default=True)
    sat = ndb.BooleanProperty(default=True)
    sun = ndb.BooleanProperty(default=True)
    time_day = ndb.StringProperty(default="ape")



#Event related models-------------------------------------------------------------
class Day(ndb.Model):
    '''Day -- Day object (nested in Event object)'''
    date_start = ndb.DateTimeProperty(required=True)
    date_end = ndb.DateTimeProperty(required=True)
    day = ndb.StringProperty(required=True)

class Event(ndb.Model):
    '''Event -- Event object'''
    #cannot have '/' in title
    e_title = ndb.StringProperty(required=True)
    e_orig_title = ndb.StringProperty(required=True)
    e_title_index = ndb.StringProperty(repeated=True)
    e_desc = ndb.TextProperty()
    e_organizer = ndb.StringProperty(required=True)
    e_location = ndb.GeoPtProperty()
    e_photo = ndb.TextProperty()
    e_id = ndb.StringProperty()
    num_attendees = ndb.IntegerProperty(default=0)
    num_teams = ndb.IntegerProperty(default=0)
    num_pending_attendees = ndb.IntegerProperty(default=0)
    num_pending_teams = ndb.IntegerProperty(default=0)
    capacity = ndb.IntegerProperty()
    sched = ndb.StructuredProperty(Day, repeated=True)
    street = ndb.StringProperty(required=True, indexed=False)
    city = ndb.StringProperty(required=True)
    state = ndb.StringProperty(required=True)
    zip_code = ndb.StringProperty(required=True)
    env = ndb.StringProperty(required=True, choices=['o', 'i', 'b'])
    funds_raised = ndb.IntegerProperty(default=0)
    req_skills = ndb.StringProperty(repeated=True)
    interests = ndb.StringProperty(repeated=True)
    education= ndb.StringProperty()
    privacy = ndb.StringProperty(required=True,choices=['o','p'])
    qr = ndb.TextProperty()
    discard_flag = ndb.IntegerProperty(default=0)

class E_Roster(ndb.Model):
    '''E_Roster -- E_Roster object (child of Event object)'''
    teams = ndb.StringProperty(repeated=True)
    e_id = ndb.StringProperty()
    e_title = ndb.StringProperty()
    attendees = ndb.StringProperty(repeated=True)
    pending_attendees = ndb.StringProperty(repeated=True)
    pending_teams = ndb.StringProperty(repeated=True)
    signed_in_attendees = ndb.StringProperty(repeated=True)
    sign_in_times = ndb.DateTimeProperty(repeated=True)
    signed_out_attendees = ndb.StringProperty(repeated=True)
    sign_out_times = ndb.DateTimeProperty(repeated=True)
    leaders = ndb.StringProperty(repeated=True)
    total_sign_in = ndb.IntegerProperty(default = 0)
    total_hours = ndb.FloatProperty(default = 0)

class E_Updates(ndb.Model):
    '''E_Updates -- E_Updates object (reference to Event object)'''
    update = ndb.StringProperty(repeated=True)
    u_datetime = ndb.DateTimeProperty(repeated=True)


class EventHistory(ndb.Model):
    '''Event -- Event object'''
    #cannot have '/' in title
    e_title = ndb.StringProperty(required=True)
    e_orig_title = ndb.StringProperty(required=True)
    e_title_index = ndb.StringProperty(repeated=True)
    e_organizer = ndb.StringProperty(required=True)
    sched = ndb.StructuredProperty(Day, repeated=True)
    street = ndb.StringProperty(required=True, indexed=False)
    city = ndb.StringProperty(required=True)
    state = ndb.StringProperty(required=True)
    funds_raised = ndb.IntegerProperty(default=0)
    registered_attendees = ndb.StringProperty(repeated=True)
    signed_in_attendees = ndb.StringProperty(repeated=True)
    average_att_hours = ndb.FloatProperty()






#Team related models--------------------------------------------------------------
class T_History(ndb.Model):
    '''T_History -- T_History object (nested in Team object) ''' 
    event = ndb.StringProperty(required=True)
    date = ndb.DateProperty()
    hours = ndb.FloatProperty()

class Team(ndb.Model):
    '''Team -- Team object ''' 
    #cannot have "/" in name
    t_name = ndb.StringProperty(required=True)
    t_orig_name = ndb.StringProperty(required=True)
    t_name_index = ndb.StringProperty(repeated=True)
    t_desc = ndb.TextProperty()
    t_photo = ndb.TextProperty()
    t_organizer = ndb.StringProperty(required=True)
    #t_capacity = ndb.IntegerProperty()
    t_members = ndb.IntegerProperty(default=0)
    t_pending_members = ndb.IntegerProperty(default=0)
    #need hist attendees separate from history for constraint reasons
    history = ndb.StructuredProperty(T_History, repeated=True)
    hist_attendees = ndb.StringProperty(repeated=True)
    funds_raised = ndb.IntegerProperty(default=0)
    t_privacy = ndb.StringProperty(required=True,choices=['o','p'])
    registered_events = ndb.StringProperty(repeated=True)
    pending_events = ndb.StringProperty(repeated=True)

class T_Roster(ndb.Model):
    '''T_Roster -- T_Roster object (child of Team object) ''' 
    leaders = ndb.StringProperty(repeated=True)
    members = ndb.StringProperty(repeated=True)
    pending_members = ndb.StringProperty(repeated=True)





