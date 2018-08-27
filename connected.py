#Project: connectED backend
#Created by: David Ramirez
#Date: 8/16/18
#Copyright 2018 LeapWithAlice,LLC. All rights reserved

#for sending HTML requests to auth0------------------------------------------
import urllib2
import urllib
import json
#----------------------------------------------------------------------------

from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import EMPTY_REQUEST
from models import ProfileCreateForm
from models import PROF_DEL_REQUEST
from models import PROF_GET_REQUEST
from models import EmailResponse
from models import Sched
from models import Profile
from models import ProfileEditForm
from models import ProfileGetResponse
from models import Event
from models import EventCreateForm
from models import EventEditForm
from models import EVENT_DEL_REQUEST
from models import EventGetResponse
from models import Day
from models import E_Roster
from models import EventNameResponse
from models import EventAddLeaders
from models import EVENT_ADD_LEADERS_REQUEST
from models import addEventLeadersResponse
from models import EVENT_DELETE_LEADERS_REQUEST
from models import GetEventsInRadiusResponse
from models import TeamCreateForm
from models import Team
from models import T_Roster
from models import TEAM_DEL_REQUEST
from models import TeamEditForm
from models import TeamGetResponse
from models import EVENT_SEARCH_REQUEST
from models import EventSearchResponse
from models import EventRosterGetResponse
from models import TeamRosterGetResponse
from models import E_Updates
from models import EventUpdatesGetResponse
#from models import TEAM_EVENT_REG_REQUEST
from models import EVENT_APPROVE_REQUEST
#from models import TEAM_EVENT_DEREG_REQUEST
from models import APPROVE_TEAM_MEMBERS_REQUEST
#from models import TeamEventRegRequest
from models import EmptyResponse
#from models import APPROVE_PENDING_TEAMS_REQUEST
from models import QR_SIGNIN_REQUEST
from models import EventHistory
from models import REGISTER_EVENT_REQUEST
from models import GetProfileEvents
from models import GetEventsInRadiusByDateResponse
from models import GetProfileTeamsResponse

import googlemaps

#DEV
gmaps = googlemaps.Client(key='AIzaSyCrZp3YMdQa6YNO7HzrD-aZ-57zp0QYDCg')
#RELEASE
#gmaps = googlemaps.Client(key='AIzaSyBfg21DtyK1K-sFvoGdziNm-zbmfx2hS74')

#firebase client ID DEV
FIREBASE_ID = "118742092535-k49n78fln2psmi584cldjkd319rsdjnf.apps.googleusercontent.com"
#firebase client ID RELEASE
#FIREBASE_ID = 32366828803-g14dan8j9m1dhises6namb5vpebopgpd.apps.googleusercontent.com

@endpoints.api(name='connected', version='v1', allowed_client_ids=[FIREBASE_ID],issuers={'firebase': endpoints.Issuer('https://securetoken.google.com/connected-dev-214119','https://www.googleapis.com/service_accounts/v1/metadata/x509/securetoken@system.gserviceaccount.com')})#,  issuers={'serviceAccount': endpoints.Issuer('fleet-fortress-211105@appspot.gserviceaccount.com','https://www.googleapis.com/robot/v1/metadata/x509/fleet-fortress-211105@appspot.gserviceaccount.com')},audiences={'serviceAccount': ['https://www.googleapis.com/oauth2/v4/token']})
#, issuers={'auth0': endpoints.Issuer('https://connected-app.auth0.com','https://connected-app.auth0.com/.well-known/jwks.json')}, audiences=[ANDROID_AUDIENCE])
class connectEDApi(remote.Service):
  """connectED API v1."""

##################################################################################
##################            HELPER FUNCTIONS              ######################
##################################################################################

  #***HELPER FUNCTION: AUTHENTICATE USER***
  #Description: make sure that user has an account. if the user does not have an account, raise exception. 
  #Params: endpoints user object
  #Returns: none
  #Called by: any endpoint
  def _authenticateUser(self):
    user = endpoints.get_current_user()
    if not user:
      raise endpoints.UnauthorizedException('Authorization required')
    return user

  #***HELPER FUNCTION: CREATE NEW TEAM***
  #Description: create a new team if one does not already exist
  #Params: request- POST request sent to createTeam() endpoint (team info)
  #Returns: request- POST request sent to createTeam() endpoint (team info)
  #Called by: createTeam() endpoint
  @ndb.transactional(xg=True)
  def _uploadNewTeam(self, request, user):
    team_name = getattr(request, 't_name')
    url_safe_name = team_name.replace(" ", "+")
    t_key = ndb.Key(Team, url_safe_name)
    team = t_key.get()
    #if team already exists, raise exception
    if team:
      raise endpoints.BadRequestException('Team name already taken')
    #if team does not exist, create new team and child schedule and store in Datastore
    else:
      profile_entity = ndb.Key(Profile, user.email()).get()
      profile_entity.created_teams.append(getattr(request, 't_name'))
      profile_entity.created_teams_id.append(url_safe_name)

      name_split = getattr(request, 't_name')
      name_split =name_split.split()

      team = Team(
        key = t_key,
        t_name = getattr(request, 't_name'),
        t_orig_name = url_safe_name,
        t_name_index = name_split,
        t_desc = getattr(request, 't_desc'),
        t_photo = getattr(request, 't_photo'),
        t_organizer = profile_entity.email,
        #t_capacity = getattr(request, 't_capacity'),
        t_privacy = getattr(request, 't_privacy')
      )

      team_roster = T_Roster(parent = t_key)
      team_roster.t_name = team.t_name
      team_roster.t_orig_name = url_safe_name

      team_roster.put()
      team.put()
      profile_entity.put()
  
    return EmptyResponse()


  #***HELPER FUNCTION: GET TEAM***
  #Description: retrieve info for a specified team
  #Params: request- GET request url portion sent to getTeam() endpoint (url safe original team name)
  #Returns: specified team info
  #Called by: getTeam() endpoint
  def _viewTeam(self, request):
    decoded_team_name = request.url_team_orig_name
    decoded_team_name = decoded_team_name.replace(" ", "+")
    #decoded_team_name = urllib.unquote(str(decoded_team_name)).decode("utf-8")
    team_entity = ndb.Key(Team, decoded_team_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('Could not find team')

    response = TeamGetResponse(
      t_name = team_entity.t_name,
      t_orig_name = team_entity.t_orig_name,
      t_organizer = team_entity.t_organizer,
      t_members = team_entity.t_members,
      t_pending_members = team_entity.t_pending_members,
      t_privacy = team_entity.t_privacy,
      funds_raised = team_entity.funds_raised
    )
    temp_t_desc = team_entity.t_desc
    if temp_t_desc:
      setattr(response, 't_desc', temp_t_desc)
    
    temp_t_photo = team_entity.t_photo
    if temp_t_photo:
      setattr(response, 't_photo', temp_t_photo)
    """
    temp_t_cap = team_entity.t_capacity
    if temp_t_cap:
      setattr(response, 't_capacity', temp_t_cap)
    """
    return response
  
  #***HELPER FUNCTION: GET TEAM ROSTER***
  #Description: retrieve info for a specified team roster
  #Params: request- GET request url portion sent to getTeamRoster() endpoint (url safe original team name)
  #Returns: specified team roster info
  #Called by: getTeamRoster() endpoint
  def _viewTeamRoster(self, request):
    decoded_name = request.url_team_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    team_roster_entity = T_Roster.query(ancestor = ndb.Key(Team, decoded_name)).get()
    if not team_roster_entity:
      raise endpoints.NotFoundException('Could not find team roster')
    
    response = TeamRosterGetResponse(
      leaders = team_roster_entity.leaders,
      members = team_roster_entity.members,
      pending_members = team_roster_entity.pending_members
    )

    return response

  
  
  #***HELPER FUNCTION: EDIT TEAM***
  #Description: make sure the logged in user is the organizer of the team and then edit the team
  #Params: request- PUT request sent to editTeam endpoint (team info to change)
  #Returns: request- PUT request sent to editTeam endpoint (team info to change)
  #Called by: editTeam endpoint
  @ndb.transactional(xg=True)
  def _editExistingTeam(self,request,user):
    #get logged in users profile entity
    user_email = user.email()

    #get the specified team entity
    original_team_name = getattr(request, 't_orig_name')
    original_team_name = original_team_name.replace(" ", "+")
    team_entity = ndb.Key(Team, original_team_name).get()

    if not team_entity:
      raise endpoints.NotFoundException('Team not found')
    if team_entity.t_organizer != user_email:
      raise endpoints.UnauthorizedException('Only team organizer can edit team')

    team_roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not team_roster_entity:
      raise endpoints.NotFoundException('Team roster not found')

    #check each message field, if it exists, change the profile property to its value
    teamName = getattr(request,'t_name')
    urlsafe_teamName = teamName.replace(" ", "+")
    proposed_team_entity = ndb.Key(Team, urlsafe_teamName).get()
    if proposed_team_entity:
      raise endpoints.BadRequestException('Team name already being used')
    if teamName:
      name_split = teamName.split()
      team_entity.t_name = teamName
      team_entity.t_name_index = name_split

      team_roster_entity.t_name = teamName

    teamDesc = getattr(request,'t_desc')
    if teamDesc:
      team_entity.t_desc = teamDesc

    teamPhoto = getattr(request,'t_photo')
    if teamPhoto:
      team_entity.t_photo = teamPhoto
    
    privacy = getattr(request,'t_privacy')
    if privacy:
      team_entity.t_privacy = privacy

      #if changing to open (public) event, convert all pending
      #attendees to attendees as long as there is capacity
      if privacy == 'o':
        if team_roster_entity:
          team_roster_entity.members.append(team_roster_entity.pending_members)
          team_roster_entity.pending_members = None
          team_entity.t_members += team_entity.t_pending_members
          team_entity.t_pending_members = 0
    
    team_entity.put()
    team_roster_entity.put()

    return EmptyResponse()
  

  #***HELPER FUNCTION: REMOVE TEAM***
  #Description: remove a team entity if it exists
  #Params: request- DELETE request query string sent to deleteTeam() endpoint (url safe original team name)
  #Returns: name of deleted team
  #Called by: deleteTeam() endpoint
  @ndb.transactional(xg=True)
  def _removeTeam(self, request,user):
    #get profile of logged in user
    decoded_email = user.email()
    #decoded_email = urllib.unquote(str(decoded_email)).decode("utf-8")
    profile_entity = ndb.Key(Profile, decoded_email).get()
    #get team entity of team to be deleted
    decoded_team_name = request.url_team_orig_name
    decoded_team_name = decoded_team_name.replace(" ", "+")
    #decoded_team_name = urllib.unquote(str(decoded_team_name)).decode("utf-8")
    team_entity = ndb.Key(Team, decoded_team_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('Team not found')
    else:
      #check that caller is organizer of team
      if team_entity.t_organizer != profile_entity.email:
        raise endpoints.UnauthorizedException('Authorization required')
      team_name = team_entity.t_name
      #get roster child of team entity
      roster_entity = T_Roster.query(ancestor=team_entity.key).get()
      #if there is a roster for the team, delete it
      if roster_entity:
        roster_entity.key.delete()
      
      #remove team from profile created teams property
      profile_entity.created_teams.remove(decoded_team_name)
      profile_entity.put()
      #delete the event
      team_entity.key.delete()

    return EmptyResponse()


  #***HELPER FUNCTION: REGISTER LOGGED IN USER TO TEAM***
  #Description: registers user for team
  #Params: request- PUT request sent to registerForTeam() endpoint (original team name)
  #Returns: name of team signed up for
  #Called by: registerForTeam() endpoint
  @ndb.transactional(xg=True)
  def _signUpTeam(self,request,user):
    user_email = user.email()
    t_name = request.url_team_orig_name
    t_name = t_name.replace(" ", "+")

    team_entity = ndb.Key(Team, t_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('could not find team')
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find team roster')
    for member in roster_entity.members:
      if member == user_email:
        raise endpoints.BadRequestException('User already signed up for team')
    """
    team_cap = team_entity.t_capacity
    if team_cap:
      if team_entity.t_members < team_cap:
        if team_entity.t_privacy == 'o':
          roster_entity.members.append(profile_entity.email)
          team_entity.t_members += 1
        elif team_entity.t_privacy == 'p':
          roster_entity.pending_members.append(profile_entity.email)
          team_entity.t_pending_members += 1
      else:
        raise endpoints.BadRequestException('Cannot register for team: at capacity')
    else:
    """
    if team_entity.t_privacy == 'o':
      roster_entity.members.append(profile_entity.email)
      team_entity.t_members += 1
    elif team_entity.t_privacy == 'p':
      roster_entity.pending_members.append(profile_entity.email)
      team_entity.t_pending_members += 1

    '''
    #1)Checks that all registered events have not been deleted, if deleted, remove from list
    #2)if registered event exists and is "open", sign user up for event because they signed up for an "event registered" team
    if team_entity.registered_events:
      for event in team_entity.registered_events:
        this_event_entity = ndb.Key(Event, event).get()
        if not this_event_entity:
          team_entity.registered_events.remove(event)
        else:
          if this_event_entity.privacy == 'o':
            #get event roster entity
            this_event_roster = E_Roster.query(ancestor=this_event_entity.key).get()
            #add user that signed up for team to event as well (because team was already registered for event)
            this_event_entity.num_attendees += 1
            this_event_roster.attendees.append(profile_entity.email)
            this_event_entity.put()
            this_event_roster.put()
    '''
    team_entity.put()
    roster_entity.put()
    return EmptyResponse()


  #***HELPER FUNCTION: DEREGISTER LOGGED IN USER FROM TEAM***
  #Description: deregisters user for team
  #Params: request- DELETE request sent to deregisterForTeam() endpoint (original team name)
  #Returns: name of team signed up for
  #Called by: deregisterForTeam() endpoint
  @ndb.transactional(xg=True)
  def _signOutTeam(self,request,user):
    user_email = user.email()
    t_name = request.url_team_orig_name
    t_name = t_name.replace(" ", "+")

    team_entity = ndb.Key(Team, t_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('could not find team')
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find team roster')

    if team_entity.t_privacy == 'o':
      check = 0
      for member in roster_entity.members:
        if member == user_email:
          check = 1
      if check == 1:
        roster_entity.members.remove(user_email)
        team_entity.t_members -= 1
      else:
        raise endpoints.BadRequestException('User already deregistered from team')
    elif team_entity.t_privacy == 'p':
      check = 0
      check2=0
      for member in roster_entity.pending_members:
        if member == user_email:
          check = 1
      for member in roster_entity.members:
        if member == user_email:
          check2 = 1
      if check == 1:
        roster_entity.pending_members.remove(user_email)
        team_entity.t_pending_members -= 1
      elif check2 == 1:
        roster_entity.members.remove(user_email)
        team_entity.t_members -= 1
      else:
        raise endpoints.BadRequestException('User already deregistered from team')

    team_entity.put()
    roster_entity.put()
    return EmptyResponse()

  #***HELPER FUNCTION: APPROVE PENDING TEAM MEMBERS***
  #Description: approve pending team members (only team organizer)
  #Params: request- PUT request sent to teamApprovePending() endpoint (team name, list of approvals)
  #Returns: list of approvals
  #Called by: teamApprovePending() endpoint
  @ndb.transactional(xg=True)
  def _tApprovePending(self, request, user):
    #get user profile entity
    user_email = user.email()
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Profile not found')
    
    #get team entity
    t_name = request.team_name
    t_name = t_name.replace(" ", "+")
    team_entity = ndb.Key(Team, t_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('Team not found')

    #check that user is event organizer
    if user_email != team_entity.t_organizer:
      raise endpoints.UnauthorizedException('User must be team organizer')
    """
   #if members is at capacity, return error
    if team_entity.t_capacity:
      if team_entity.t_members >= team_entity.t_capacity:
        raise endpoints.BadRequestException('Team is already at capacity')
    """
    #get team roster entity
    t_roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not t_roster_entity:
      raise endpoints.NotFoundException('Team roster not found')

    #approve member 
    for member in getattr(request, 'approve_list'):
      if member in t_roster_entity.pending_members:
        t_roster_entity.pending_members.remove(member)
        t_roster_entity.members.append(member)
        team_entity.t_pending_members-=1
        team_entity.t_members+=1
        
    '''
    #register just-approved users to any events that team is already signed up for
    if team_entity.registered_events:
      for this_event in team_entity.registered_events:
        this_event_entity = ndb.Key(Event, this_event).get()
        if this_event_entity:
          this_event_roster = E_Roster.query(ancestor=this_event_entity.key).get()
          for member in getattr(request, 'approve_list'):
            if this_event_entity.num_attendees < this_event_entity.capacity:
              this_event_entity.num_attendees += 1
              this_event_roster.attendees.append(member)
          this_event_entity.put()
          this_event_roster.put()
    '''
            
              
    t_roster_entity.put()
    team_entity.put()
    
    return EmptyResponse()

  #***HELPER FUNCTION: CREATE NEW PROFILE***
  #Description: create a new profile if one does not already exist
  #Params: request- POST request sent to createProfile() endpoint (profile info)
  #Returns: request- POST request sent to createProfile() endpoint (profile info)
  #Called by: createProfile() endpoint
  @ndb.transactional()
  def _uploadNewProfile(self, request, user):
    user_email = user.email()
    p_key = ndb.Key(Profile, user_email)
    profile = p_key.get()
    #if profile already exists, raise exception
    if profile:
      raise endpoints.BadRequestException("Email is already used for existing profile")
    #if profile does not exist, create new profile and child schedule and store in Datastore
    else:
      profile = Profile(
        key = p_key,
        email = user_email,
        first_name = getattr(request, 'first_name'),
        last_name = getattr(request, 'last_name'),
        location = ndb.GeoPt(getattr(request, 'lat'), getattr(request, 'lon')),
        interests = getattr(request, 'interests'),
        education = getattr(request, 'education'),
        skills = getattr(request, 'skills'),
        photo = getattr(request, 'photo')
      )
      profile.put()

      schedule = Sched(
        parent = p_key,
        mon = getattr(request, 'mon'),
        tue = getattr(request, 'tue'),
        wed = getattr(request, 'wed'),
        thu = getattr(request, 'thu'),
        fri = getattr(request, 'fri'),
        sat = getattr(request, 'sat'),
        sun = getattr(request, 'sun'),
        time_day = getattr(request, 'time_day')
      )
      schedule.put()

      return EmptyResponse()

  #***HELPER FUNCTION: GET PROFILE***
  #Description: retrieve info for a specified profile
  #Params: request- GET request url portion sent to getProfile() endpoint (email of profile to get)
  #Returns: specified profile core info
  #Called by: getProfile() endpoint
  def _viewProfile(self, request, user):
    decoded_email_to_get = request.email_to_get
    profile_entity = ndb.Key(Profile, decoded_email_to_get).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Could not find profile in database')

    response = ProfileGetResponse(
      first_name = profile_entity.first_name,
      last_name = profile_entity.last_name,
      lat = profile_entity.location.lat,
      lon = profile_entity.location.lon,
      interests = profile_entity.interests,
      education = profile_entity.education,
      skills = profile_entity.skills,
      photo = profile_entity.photo,
    )
    return response

  #***HELPER FUNCTION: GET PROFILE EVENTS***
  #Description: retrieve event info for a profile
  #Params: request- GET request url portion sent to getProfileEvents() endpoint 
  #Returns: specified profile's event info
  #Called by: getProfileEvents() endpoint
  def _viewProfileEvents(self, request, user):
    #get profile entity
    profile_entity = ndb.Key(Profile, request.email_to_get).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Could not find profile in database')
    
    #declare reponse and fill out completed_events and created_events
    response = GetProfileEvents(
      completed_events = profile_entity.completed_events,
      created_events = profile_entity.created_events
    )
    #append any currently attending events to completed events
    response.completed_events +=profile_entity.attended_events
    
    #get all registered future events and save to reponse
    event_roster_list = E_Roster.query(E_Roster.attendees == profile_entity.email)
    for roster in event_roster_list:
      response.registered_events.append(roster.e_id)

    for event in response.completed_events:
      if event in response.registered_events:
        response.registered_events.remove(event)

    return response


  #***HELPER FUNCTION: GET PROFILE TEAMS***
  #Description: retrieve teams info for a profile
  #Params: request- GET request url portion sent to getProfileTeams() endpoint 
  #Returns: specified profile's team info
  #Called by: getProfileTeams() endpoint
  def _viewProfileTeams(self, request, user):
    #get profile entity
    profile_entity = ndb.Key(Profile, request.email_to_get).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Could not find profile in database')
    
    #declare reponse and fill out created_teams 
    response = GetProfileTeamsResponse(
      created_team_names = profile_entity.created_teams,
      created_team_ids = profile_entity.created_teams_ids
    )
    
    #get all teams user is registered to
    registered_team_rosters = T_Roster.query(T_Roster.members == profile_entity.email).fetch()
    if registered_team_rosters:
      for team_roster in registered_team_rosters:
        response.registered_team_names.append(team_roster.t_name)
        response.registered_team_ids.append(team_roster.t_orig_name)
    
    #get all teams user is pending registration 
    pending_team_rosters = T_Roster.query(T_Roster.pending_members == profile_entity.email).fetch()
    if pending_team_rosters:
      for team_roster in pending_team_rosters:
        response.pending_team_names.append(team_roster.t_name)
        response.pending_team_ids.append(team_roster.t_orig_name)
    
    #get all teams user is leader of
    leader_team_rosters = T_Roster.query(T_Roster.leaders == profile_entity.email).fetch()
    if leader_team_rosters:
      for team_roster in leader_team_rosters:
        response.leader_team_names.append(team_roster.t_name)
        response.leader_team_ids.append(team_roster.t_orig_name)

    return response

  
  #***HELPER FUNCTION: EDIT PROFILE OF LOGGED IN USER***
  #Description: make sure the logged in user is the owner of the account and then edit the account
  #Params: request- PUT request sent to editProfile endpoint (profile info to change)
  #Returns: request- PUT request sent to editProfile endpoint (profile info to change)
  #Called by: editProfile endpoint
  @ndb.transactional()
  def _editExistingProfile(self, request, user):
    user_email = user.email()
    #raise endpoints.BadRequestException(user_email)
    #get logged in users profile entity
    p_key = ndb.Key(Profile, user_email)
    profile_entity = p_key.get()

    #get schedule that correponds with logged in users profile
    schedule_entity = Sched.query(ancestor=p_key).get()

    #check each message field, if it exists, change the profile property to its value
    new_pass = getattr(request, 'new_password')
    if new_pass:
      profile_entity.passwrd = new_pass
    
    firstName = getattr(request,'first_name')
    if firstName:
      profile_entity.first_name = firstName

    lastName = getattr(request,'last_name')
    if lastName:
      profile_entity.last_name = lastName

    latitude = getattr(request,'lat')
    longitude = getattr(request, 'lon')
    if latitude and longitude:
      profile_entity.location = ndb.GeoPt(latitude, longitude)

    #completely replaces interests (if interests are passed)
    interests = getattr(request,'interests')
    if interests:
      profile_entity.interests = interests

    education = getattr(request,'education')
    if education:
      profile_entity.education = education

    skills = getattr(request,'skills')
    if skills:
      profile_entity.skills = skills

    monday = getattr(request,'mon')
    if monday:
      schedule_entity.mon = monday
    
    tuesday = getattr(request,'tue')
    if tuesday:
      schedule_entity.tue = tuesday
    
    wednesday = getattr(request,'wed')
    if wednesday:
      schedule_entity.wed = wednesday

    thursday = getattr(request,'thu')
    if thursday:
      schedule_entity.thu = thursday
    
    friday = getattr(request,'fri')
    if friday:
      schedule_entity.fri = friday
    
    saturday = getattr(request,'sat')
    if saturday:
      schedule_entity.sat = saturday

    sunday = getattr(request,'sun')
    if monday:
      schedule_entity.sun = sunday
    
    timeOfDay = getattr(request, 'time_day')
    if timeOfDay:
      schedule_entity.time_day = timeOfDay

    pic = getattr(request,'photo')
    if pic:
      profile_entity.photo = pic
    
    profile_entity.put()
    schedule_entity.put()

    return EmptyResponse()


  #***HELPER FUNCTION: REMOVE PROFILE***
  #Description: remove a profile entity if it exists
  #Params: request- DELETE request query string sent to deleteProfile() endpoint (profile email)
  #Returns: request- DELETE request query string sent to deleteProfile() endpoint (profile email)
  #Called by: deleteProfile() endpoint
  @ndb.transactional()
  def _removeProfile(self, request, user):
    decoded_email = user.email()
    #decoded_email = urllib.unquote(str(decoded_email)).decode("utf-8")
    profile = ndb.Key(Profile, decoded_email).get()
    #if profile does not exist, raise exception
    if not profile:
      raise endpoints.BadRequestException
    #if profile does exist, delete it from Datastore
    else:
      schedule = Sched.query(ancestor=profile.key).get()
      profile.key.delete()
      if schedule:
        schedule.key.delete()

    return EmptyResponse()

  
  #***HELPER FUNCTION:  CREATE NEW EVENT***
  #Description: create a new event registered under the logged in user
  #Params: request- POST request sent to any createEvent endpoint (event info)
  #Returns: request- POST request sent to any createEvent endpoint (event info)
  #Called by: createEvent endpoint
  @ndb.transactional(xg=True)
  def _createEvent(self, request, user):
    #get profile entity
    profile_entity = ndb.Key(Profile, user.email()).get()

    #get event entity
    event_id = user.email()
    temp_title = getattr(request,'e_title')
    url_safe_title = temp_title.replace(" ", "+")
    event_id += '_' + url_safe_title
    e_key = ndb.Key(Event, event_id)
    event = e_key.get()
    profile_entity.created_events.append(event_id)
    #if event_id already exists, raise exception (one user cannot create 2 events with the same name)
    if event:
      raise endpoints.BadRequestException('Cannot create 2 events with the same name')
    # create new Event if not there
    else:
      event = Event(
        key = e_key,
        e_title = getattr(request, 'e_title'),
        e_orig_title = url_safe_title,
        e_desc = getattr(request, 'e_desc'),
        e_organizer = user.email(),
        e_photo = getattr(request, 'e_photo'),
        capacity = getattr(request, 'capacity'),
        street = getattr(request, 'street'),
        city = getattr(request, 'city'),
        state = getattr(request, 'state'),
        zip_code = getattr(request, 'zip_code'),
        env = getattr(request, 'env'),
        req_skills = getattr(request, 'req_skills'),
        interests = getattr(request, 'interests'),
        education= getattr(request, 'education'),
        privacy = getattr(request, 'privacy'),
        qr = getattr(request, 'qr'),
      )

      title_split = getattr(request, 'e_title')
      title_split =title_split.split()
      event.e_title_index = title_split
      this_day = getattr(request, 'day')
      this_start = getattr(request, 'start')
      this_end = getattr(request, 'end')

      counter = 0
      #for each scheduled day the event will be active
      for date in getattr(request, 'date'):
        #save date object
        date_object = datetime.strptime(date, '%Y-%m-%d')
        date_object = date_object.date()
        #save time objects
        start_time_object = datetime.strptime(this_start[counter], '%H:%M').time()
        end_time_object = datetime.strptime(this_end[counter], '%H:%M').time()
        #calculate time difference
        full_start = date + this_start[counter]
        full_end = date + this_end[counter]
        start_dt = datetime.strptime(full_start, '%Y-%m-%d%H:%M')
        end_dt = datetime.strptime(full_end, '%Y-%m-%d%H:%M')
        
        event.sched += [
          Day(
            date_start = start_dt,
            date_end = end_dt,
            day = this_day[counter]
          )]    
        counter += 1

      #get lat and lon for event
      geocode_result = gmaps.geocode(getattr(event, 'street')+','+ getattr(event, 'city')+','+getattr(event,'state'))
      if not geocode_result:
        raise endpoints.BadRequestException('Event address could not be located')
      this_location = geocode_result[0]
      this_lat = this_location['geometry']['location']['lat']
      this_lon = this_location['geometry']['location']['lng']

      setattr(event, 'e_location', ndb.GeoPt(this_lat, this_lon))

      roster = E_Roster(parent = e_key)
      roster.e_id = event_id
      roster.e_title = event.e_title
      event.e_id = event_id
      updates = E_Updates(parent = e_key)
      updates.put()
      roster.put()
      event.put()
      profile_entity.put()
    return EmptyResponse()
  

  #***HELPER FUNCTION: GET EVENT***
  #Description: retrieve info for a specified event
  #Params: request- GET request url portion sent to getEvent() endpoint (url safe original event name)
  #Returns: specified event info
  #Called by: getEvent() endpoint
  def _viewEvent(self, request):
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    event_id = request.e_organizer_email + '_' + decoded_name
    event_entity = ndb.Key(Event, event_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Could not find event')

    #create response object
    response = EventGetResponse(
      e_orig_title = event_entity.e_orig_title,
      e_title = event_entity.e_title,
      e_organizer = event_entity.e_organizer,
      e_desc = event_entity.e_desc,
      e_photo = event_entity.e_photo,
      e_lat = event_entity.e_location.lat,
      e_lon = event_entity.e_location.lon,
      capacity = event_entity.capacity,
      street = event_entity.street,
      city = event_entity.city,
      state = event_entity.state,
      zip_code = event_entity.zip_code,
      env = event_entity.env,
      req_skills = event_entity.req_skills,
      interests = event_entity.interests,
      education= event_entity.education,
      privacy = event_entity.privacy,
      qr = event_entity.qr,
      num_attendees = event_entity.num_attendees,
      funds_raised = event_entity.funds_raised,
      num_pending_attendees = event_entity.num_pending_attendees
    )

    this_sched = getattr(event_entity, "sched")
    for this_day in this_sched:
      date_object = this_day.date_start
      date_string = date_object.strftime('%m/%d/%Y')
      start_object = date_object
      start_string = start_object.strftime('%H:%M')
      end_object = this_day.date_end
      end_string = end_object.strftime('%H:%M')
      response.date.append(date_string)
      response.day.append(this_day.day)
      response.start.append(start_string)
      response.end.append(end_string)

    return response
  
  #***HELPER FUNCTION: GET EVENT ROSTER***
  #Description: retrieve info for a specified event roster
  #Params: request- GET request url portion sent to getEventRoster() endpoint (url safe original event name)
  #Returns: specified event roster info
  #Called by: getEventRoster() endpoint
  def _viewEventRoster(self, request):
    #convert name in request params to event_id
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    event_id = request.e_organizer_email + '_' + decoded_name
    #get event and event roster entities
    event_entity = ndb.Key(Event, event_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Could not find event')
    event_roster_entity = E_Roster.query(ancestor = ndb.Key(Event, event_id)).get()
    if not event_roster_entity:
      raise endpoints.NotFoundException('Could not find event roster')
    
    #fill out return reponse of event roster
    response = EventRosterGetResponse(
      teams = event_roster_entity.teams,
      attendees = event_roster_entity.attendees,
      pending_attendees = event_roster_entity.pending_attendees,
      signed_in_attendees = event_roster_entity.signed_in_attendees,
      signed_out_attendees = event_roster_entity.signed_out_attendees,
      leaders = event_roster_entity.leaders,
      organizer = event_entity.e_organizer
    )

    #return event roste info
    return response


  #***HELPER FUNCTION: GET EVENT UPDATES***
  #Description: retrieve info for a specified event updates
  #Params: request- GET request url portion sent to getEventUpdates() endpoint (url safe original event name)
  #Returns: specified event updates info
  #Called by: getEventUpdates() endpoint
  def _viewEventUpdates(self, request):
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    event_id = request.e_organizer_email + '_' + decoded_name
    event_updates_entity = E_Updates.query(ancestor = ndb.Key(Event, event_id)).get()
    if not event_updates_entity:
      raise endpoints.NotFoundException('Could not find event updates')
    
    response_dates = []
    for date in event_updates_entity.u_datetime:
      response_dates.append(date.strftime('%m/%d/%Y-%H:%M'))
    
    response = EventUpdatesGetResponse(
      updates = event_updates_entity.update,
      u_datetime = response_dates
    )
  
    return response


  #***MINI HELPER FUNCTION: UPDATE E_UPDATES ENITITY***
  def _modUpdates(self, update, u_entity):
    if len(u_entity.update) >= 30:
      u_entity.update.pop(0)
      u_entity.u_datetime.pop(0)
    u_entity.update.append(update)
    udt = datetime.now()
    u_entity.u_datetime.append(udt)

  #***HELPER FUNCTION: EDIT EVENT OF AUTHORIZED USER***
  #Description: make sure the logged in user is creator or leader of event and edit event
  #Params: request- PUT request sent to editEvent endpoint (event info to change)
  #Returns: request- PUT request sent to editEvent endpoint (event info to change)
  #Called by: editEvent endpoint
  @ndb.transactional(xg=True)
  def _editExistingEvent(self, request, user):
    #get profile of logged in user
    profile_entity = ndb.Key(Profile, user.email()).get()
    #get event entity of event to be edited
    e_title = getattr(request, 'e_orig_title')
    e_title = e_title.replace(" ", "+")
    event_id = user.email() + '_'+ e_title
    event_entity = ndb.Key(Event, event_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')
    else:
      #get e_updates entity 
      updates_entity = E_Updates.query(ancestor=event_entity.key).get()
      if not updates_entity:
        raise endpoints.NotFoundException('Event updates not found')
      #if the logged in user is not the event organizer, check to see if they are an event leader
      if event_entity.e_organizer != profile_entity.email:
        #leaderCheck = 0
      #  if roster_entity:
        #  for leader in roster_entity.leaders:
        #    if leader == profile_entity.email:
        #     leaderCheck = 1
        #if leaderCheck == 0:
        raise endpoints.UnauthorizedException('Authorization required')

      e_title = getattr(request,'e_title')
      if e_title:
        title_split = e_title.split()
        event_entity.e_title = e_title
        event_entity.e_title_index = title_split
        #get event roster entity
        event_roster = E_Roster.query(ancestor = event_entity.key).get()
        event_roster.e_title = e_title

        update = 'Event title updated'
        self._modUpdates(update, updates_entity)
      
      e_desc = getattr(request,'e_desc')
      if e_desc:
        event_entity.e_desc = e_desc

        update = 'Event description updated'
        self._modUpdates(update, updates_entity)
      
      e_photo = getattr(request,'e_photo')
      if e_photo:
        event_entity.e_photo = e_photo

        update = 'Event photo updated'
        self._modUpdates(update, updates_entity)

      capacity = getattr(request,'capacity')
      if capacity:
        event_entity.capacity = capacity

        update = 'Event capacity updated'
        self._modUpdates(update, updates_entity)

      street = getattr(request,'street')
      if street:
        event_entity.street = street

        update = 'Event location updated'
        self._modUpdates(update, updates_entity)

      city = getattr(request,'city')
      if city:
        event_entity.city = city

      state = getattr(request,'state')
      if state:
        event_entity.state = state

      zip_code = getattr(request,'zip_code')
      if zip_code:
        event_entity.zip_code = zip_code

      env = getattr(request,'env')
      if env:
        event_entity.env = env

        update = 'Event setting updated'
        self._modUpdates(update, updates_entity)

      req_skills = getattr(request,'req_skills')
      if req_skills:
        event_entity.req_skills = req_skills

        update = 'Event required skills updated'
        self._modUpdates(update, updates_entity)

      interests = getattr(request,'interests')
      if interests:
        event_entity.interests = interests

        update = 'Event interest tags updated'
        self._modUpdates(update, updates_entity)
      
      education = getattr(request,'education')
      if education:
        event_entity.education = education

        update = 'Event education level updated'
        self._modUpdates(update, updates_entity)

      privacy = getattr(request,'privacy')
      if privacy:
        event_entity.privacy = privacy

        update = 'Event privacy updated'
        self._modUpdates(update, updates_entity)

        #if changing to open (public) event, convert all pending
        #attendees to attendees as long as there is capacity
        if privacy == 'o':
          event_roster_entity = E_Roster.query(ancestor=event_entity.key).get()
          if event_roster_entity:
            if not event_entity.capacity:
              event_roster_entity.attendees.append(event_roster_entity.pending_attendees)
              event_roster_entity.pending_attendees = None
              event_entity.num_attendees += event_entity.num_pending_attendees
              event_entity.num_pending_attendees = 0
            elif event_entity.num_attendees < event_entity.capacity:
              counter = 0
              for pending_attendee in event_roster_entity.pending_attendees:
                if event_entity.num_attendees < event_entity.capacity:
                  event_roster_entity.attendees.append(pending_attendee)
                  event_entity.num_attendees += 1
                  event_entity.num_pending_attendees -= 1
                  counter += 1
                else:
                  break
              for x in range(counter):
                event_roster_entity.pending_attendees.pop()
            event_roster_entity.put()
            
      qr = getattr(request,'qr')
      if qr:
        event_entity.qr = qr

        update = 'Event QR code updated'
        self._modUpdates(update, updates_entity)
        
      date = getattr(request, 'date')
      if date:
        #clear out current scheduled days
        del event_entity.sched[:]
        #get day of week, start times, and end times
        days = getattr(request,'day')
        starts = getattr(request,'start')
        ends = getattr(request, 'end')
        counter = 0
        #for each new scheduled day, save in Datastore
        for this_date in date:
          full_start_dt = this_date + starts[counter]
          full_end_dt = this_date + ends[counter]

          start_dt_object = datetime.strptime(full_start_dt, '%Y-%m-%d%H:%M')
          end_dt_object = datetime.strptime(full_end_dt, '%Y-%m-%d%H:%M')
          event_entity.sched.append(Day(date_start = start_dt_object,date_end = end_dt_object,day = days[counter]))
                
          counter += 1

        #fill out any updates
        update = 'Event date updated'
        self._modUpdates(update, updates_entity)

        #set lat/lon again if location changed
        edited_street = getattr(request, 'street')
        edited_city = getattr(request, 'city')
        edited_state = getattr(request, 'state')

        if edited_street or edited_city or edited_state:
          geocode_result = gmaps.geocode(getattr(event_entity, 'street')+','+ getattr(event_entity, 'city')+','+getattr(event_entity,'state'))
          if not geocode_result:
            raise endpoints.BadRequestException('Event address cannot be located')
          this_location = geocode_result[0]
          this_lat = this_location['geometry']['location']['lat']
          this_lon = this_location['geometry']['location']['lng']
          event_entity.e_location = ndb.GeoPt(this_lat, this_lon)

      event_entity.put()
      updates_entity.put()
    return EmptyResponse()

  """
  #***HELPER FUNCTION: REGISTER TEAM TO EVENT***
  #Description: registers team for event
  #Params: request- PUT request sent to registerTeamForEvent() endpoint (user email, event ID)
  #Returns: name of event signed up for
  #Called by: registerTeamForEvent() endpoint
  @ndb.transactional(xg=True)
  def _signUpTeamEvent(self, request, user):
    #to find user profile entity
    user_email = user.email()

    #to find event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title

    #to find team entity
    t_name = getattr(request, 'team')
    t_name = t_name.replace(" ", "+")

    #get event entity
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('could not find event')
    #get profile entity of user
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    #get event roster entity
    roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')
    #get team entity
    team_entity = ndb.Key(Team, t_name).get()
    if not team_entity:
      raise endpoints.NotFoundException('could not find team ')
    #get team roster entity
    team_roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not team_roster_entity:
      raise endpoints.NotFoundException('could not find team roster')

    #get capacity of team members
    t_cap = team_entity.t_capacity
    #get capacity of event
    e_cap = event_entity.capacity
    #get current number of attendees of event
    e_attendees = event_entity.num_attendees

    #ensure that event has room for team
    if (e_attendees + t_cap) > e_cap:
      raise endpoints.BadRequestException('Event does not have capacity for team')

    #depending on whether private event or not, sign team members up for event or sign
    #up team for pending teams
    if event_entity.privacy == 'p':
      #if team already registered throw error
      if team_entity.t_name in roster_entity.pending_teams:
        raise endpoints.BadRequestException('Team already registered for event')
      roster_entity.pending_teams.append(t_name)
      event_entity.num_pending_teams += 1
       #add event to pending events in team entity
      team_entity.pending_events.append(e_id)
    elif event_entity.privacy == 'o':
      #if team already registered throw error
      if team_entity.t_name in roster_entity.teams:
        raise endpoints.BadRequestException('Team already registered for event')
      roster_entity.teams.append(t_name)
      event_entity.num_attendees += t_cap
      event_entity.num_teams += 1
      #add event to registered events in team entity
      team_entity.registered_events.append(e_id)
      for member in team_roster_entity.members:
        roster_entity.attendees.append(member)
        
    
    #create update for event (only if event is private)
    if event_entity.privacy == 'o':
      updates_entity = E_Updates.query(ancestor=event_entity.key).get()
      update = team_entity.t_name + ' has joined'
      self._modUpdates(update, updates_entity)
      updates_entity.put()

    #set changes for event and roster entity
    team_entity.put()
    event_entity.put()
    roster_entity.put()

    return EmptyResponse()
    
  #***HELPER FUNCTION: DEREGISTER TEAM FROM EVENT***
  #Description: deregisters team from event
  #Params: request- DELETE request sent to deregisterTeamFromEvent() endpoint (user email, event ID)
  #Returns: name of event signed out of
  #Called by: deregisterTeamFromEvent() endpoint
  @ndb.transactional(xg=True)
  def _signOutTeamEvent(self, request, user):
    #to find user profile entity
    user_email = user.email()

    #to find event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title

    #to find team entity
    t_name = getattr(request, 'team')
    t_name = t_name.replace(" ", "+")

    #get event entity
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('could not find event')
    #get profile entity of user
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    #get event roster entity
    roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')
    #get team entity
    team_entity = ndb.Key(Team, t_name).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')
    #get team roster entity
    team_roster_entity = T_Roster.query(ancestor=team_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')

    #depending on whether private event or not, sign team members up for event or sign
    #up team for pending teams
    if event_entity.privacy == 'p':
      roster_entity.pending_teams.remove(t_name)
      event_entity.num_pending_teams -= 1
    elif event_entity.privacy == 'o':
      roster_entity.teams.remove(t_name)
      team_entity.registered_events.remove(e_id)
      event_entity.num_teams -= 1
      for member in team_roster_entity.members:
        roster_entity.attendees.remove(member)
        event_entity.num_attendees -= 1

    #set changes for event and roster entity
    team_entity.put()
    event_entity.put()
    roster_entity.put()

    return EmptyResponse()
  """

  #***HELPER FUNCTION: REGISTER LOGGED IN USER TO EVENT***
  #Description: registers user for event
  #Params: request- PUT request sent to registerForEvent() endpoint (user email, event ID)
  #Returns: name of event signed up for
  #Called by: registerForEvent() endpoint
  @ndb.transactional(xg=True)
  def _signUpEvent(self, request, user):
    user_email = user.email()
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")

    e_id = e_organizer + '_' + e_title
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('could not find event')
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')

    #if event has capacity, make sure there is room for another attendee before registering
    #if event has no cap, go ahead and register user for event
    event_cap = event_entity.capacity
    if event_cap:
      if event_entity.num_attendees < event_cap:
        if event_entity.privacy == 'o':
          for attendee in roster_entity.attendees:
            if attendee == user_email:
              raise endpoints.BadRequestException('User already registered for event')
          roster_entity.attendees.append(profile_entity.email)
          event_entity.num_attendees += 1
        elif event_entity.privacy == 'p':
          for attendee in roster_entity.pending_attendees:
            if attendee == user_email:
              raise endpoints.BadRequestException('User already registered for event')
          roster_entity.pending_attendees.append(profile_entity.email)
          event_entity.num_pending_attendees += 1
      else:
        raise endpoints.BadRequestException('Cannot sign up for event: at capacity')
    else:
      if event_entity.privacy == 'o':
        for attendee in roster_entity.attendees:
          if attendee == user_email:
            raise endpoints.BadRequestException('User already registered for event')
        roster_entity.attendees.append(profile_entity.email)
        event_entity.num_attendees += 1
      elif event_entity.privacy == 'p':
        for attendee in roster_entity.pending_attendees:
          if attendee == user_email:
            raise endpoints.BadRequestException('User already registered for event')
        roster_entity.pending_attendees.append(profile_entity.email)
        event_entity.num_pending_attendees += 1
      
    #if team choice passed and exists, register team or pending team
    team_exist_flag = 0
    team_name = ''
    if getattr(request, 'team'):
      orig_team_name = getattr(request, 'team')
      orig_team_name = orig_team_name.replace(" ", "+")
      this_team = ndb.Key(Team, orig_team_name).get()
      if this_team:
        team_exist_flag = 1
        team_name = this_team.t_name
        if event_entity.privacy == 'o':
          roster_entity.teams.append(getattr(request, 'team'))
          event_entity.num_teams += 1
        elif event_entity.privacy == 'p':
          roster_entity.pending_teams.append(getattr(request, 'team'))
          event_entity.num_pending_teams += 1
    else:
      if event_entity.privacy == 'o':
          roster_entity.teams.append('-')
      elif event_entity.privacy == 'p':
        roster_entity.pending_teams.append('-')

    #get e_updates and add update
    if event_entity.privacy == 'o':
      updates_entity = E_Updates.query(ancestor=event_entity.key).get()
      update = profile_entity.first_name+' '+profile_entity.last_name+' has joined'
      self._modUpdates(update, updates_entity)
      if getattr(request, 'team'):
        if team_exist_flag ==1:
          update = team_name +' has joined'
          self._modUpdates(update, updates_entity)
      updates_entity.put()
    
    event_entity.put()
    roster_entity.put()
    return EmptyResponse()


  #***HELPER FUNCTION: DEREGISTER LOGGED IN USER FOR EVENT***
  #Description: removes the user from the event and the event from the user
  #Params: request- original event name and organizer email; user object
  #Returns: name of event signed out of
  #Called by: deregisterForEvent() endpoint
  @ndb.transactional(xg=True)
  def _signOutEvent(self, request, user):
    user_email = user.email()
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title

    #get event entity, profile entity, and roster entity
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('could not find event')
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')
    roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')

    #get e_updates entity
    updates_entity = E_Updates.query(ancestor=event_entity.key).get()

    #deregister user from event
    if event_entity.privacy == 'o':
      if user_email in roster_entity.attendees:
        #get index of user email to find user team
        this_index = roster_entity.attendees.index(user_email)
        #also remove user team
        this_team = roster_entity.teams.pop(this_index)
        # if pending team exists, reduce pending team number
        if this_team != '-':
          event_entity.num_teams -= 1
          #create update
          this_team = this_team.replace("+", " ")
          update = this_team+' deregistered from event'
          self._modUpdates(update, updates_entity)
        roster_entity.attendees.remove(user_email)
        event_entity.num_attendees -= 1
        #create update
        update = profile_entity.first_name+' '+profile_entity.last_name+' deregistered from event'
        self._modUpdates(update, updates_entity)
      else:
        raise endpoints.BadRequestException('User already deregistered from event')
    elif event_entity.privacy == 'p':
      if user_email in roster_entity.pending_attendees:
        #get index of user email to find user team
        this_index = roster_entity.pending_attendees.index(user_email)
        #also remove user team
        this_team = roster_entity.pending_teams.pop(this_index)
        # if pending team exists, reduce pending team number
        if this_team != '-':
          event_entity.num_pending_teams -= 1
        roster_entity.pending_attendees.remove(user_email)
        event_entity.num_pending_attendees -= 1
      elif user_email in roster_entity.attendees:
        #get index of user email to find user team
        this_index = roster_entity.attendees.index(user_email)
        #also remove user team
        this_team = roster_entity.teams.pop(this_index)
        # if pending team exists, reduce pending team number
        if this_team != '-':
          event_entity.num_teams -= 1
          #create update
          this_team = this_team.replace("+", " ")
          update = this_team +' deregistered from event'
          self._modUpdates(update, updates_entity)
        roster_entity.attendees.remove(user_email)
        event_entity.num_attendees -= 1
        #create update
        update = profile_entity.first_name+' '+profile_entity.last_name+' deregistered from event'
        self._modUpdates(update, updates_entity)
      else:
        raise endpoints.BadRequestException('User already deregistered from event')

    updates_entity.put()
    event_entity.put()
    roster_entity.put()
    return EmptyResponse()

  #***HELPER FUNCTION: QR SIGN IN TO EVENT FOR USER***
  #Description: sign user into active event (to be called after qr scanning on front end)
  #Params: request- PUT request sent to qrSignInEvent() endpoint (user email, event ID)
  #Returns: name of event signed up for
  #Called by: qrSignInEvent() endpoint
  @ndb.transactional(xg=True)
  def _qrInEvent(self, request, user):
    #user user profile entity
    user_email = user.email()
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')

    #get event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title
    event_key = ndb.Key(Event, e_id)
    if not event_key:
      raise endpoints.NotFoundException('could not find event')

    #get event roster entity
    roster_entity = E_Roster.query(ancestor=event_key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')

    #make sure user is registered for event and sign user in
    check = 0
    check2 = 0
    check3 = 0
    for attendee in roster_entity.attendees:
      if attendee == user_email:
        check = 1
    for attendee2 in roster_entity.signed_in_attendees:
      if attendee2 == user_email:
        check2 = 1
    for attendee3 in roster_entity.signed_out_attendees:
      if attendee3 == user_email:
        check3 = 1
        roster_entity.signed_out_attendees.remove(attendee3)
    if check == 0:
      raise endpoints.BadRequestException('User must be registered for event to sign in')
    if check2 == 1:
      raise endpoints.BadRequestException('User already signed in')
    now = datetime.now()
    if check3 == 0:
      roster_entity.total_sign_in += 1
    roster_entity.signed_in_attendees.append(user_email)
    roster_entity.sign_in_times.append(now)

    #save qr sign in time to db to calculate hours when signed out
    sign_in_time = datetime.now()
    profile_entity.qr_in_dt = sign_in_time

    #save event id in attended events list in Profile entity
    profile_entity.attended_events.append(e_id)
    roster_entity.put()
    profile_entity.put()
    return EmptyResponse()
    
  #***HELPER FUNCTION: QR SIGN OUT FROM EVENT FOR USER***
  #Description: sign user out of active event (to be called after qr scanning on front end)
  #Params: request- DELETE request sent to qrSignOutEvent() endpoint (user email, event ID)
  #Returns: name of event signed out of
  #Called by: qrSignOutEvent() endpoint
  @ndb.transactional(xg=True)
  def _qrOutEvent(self, request, user):
    #user user profile entity
    user_email = user.email()
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('could not find profile')

    #get event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title
    event_key = ndb.Key(Event, e_id)
    if not event_key:
      raise endpoints.NotFoundException('could not find event')

    #get event roster entity
    roster_entity = E_Roster.query(ancestor=event_key).get()
    if not roster_entity:
      raise endpoints.NotFoundException('could not find event roster')
    
    #make sure user qr signed into event and qr sign user out
    check = 0
    check2 = 0
    for attendee in roster_entity.signed_in_attendees:
      if attendee == user_email:
        check = 1
    for attendee2 in roster_entity.signed_out_attendees:
      if attendee2 == user_email:
        check2 = 1
    if check == 0:
      raise endpoints.BadRequestException('user must be signed in to event to sign out')
    if check2 == 1:
      raise endpoints.BadRequestException('user already signed out')
    now = datetime.now()
    roster_entity.signed_in_attendees.remove(user_email)
    roster_entity.signed_out_attendees.append(user_email)
    roster_entity.sign_out_times.append(now)
    
    #calculate difference between sign in time and sign out time
    sign_out_time = datetime.now()
    sign_in_time = profile_entity.qr_in_dt
    elapsed = sign_out_time - sign_in_time
    hours=0
    if elapsed.days == 0:
      hours = float(elapsed.seconds)/3600
      hours = round(hours,2)
      if profile_entity.hours:
        profile_entity.hours += hours
      else:
        profile_entity.hours = hours
     
    #add hours to total event hours
    roster_entity.total_hours += hours
    

    #remove old sign in time
    profile_entity.qr_in_dt = None

    #save event id in attended events list in Profile entity
    if e_id not in profile_entity.completed_events:
      profile_entity.completed_events.append(e_id)
      profile_entity.attended_events.remove(e_id)
      profile_entity.event_hours.append(hours)
    else:
      index = profile_entity.completed_events.index(e_id)
      profile_entity.event_hours[index] += hours
    
    roster_entity.put()
    profile_entity.put()

    return EmptyResponse()

  #***HELPER FUNCTION: APPROVE PENDING EVENT ATTENDEES***
  #Description: approve pending event attendees (only event organizer)
  #Params: request- PUT request sent to eventApprovePending() endpoint (url safe original event name, event creator email, list of approvals)
  #Returns: event name
  #Called by: eventApprovePending() endpoint
  @ndb.transactional(xg=True)
  def _eApprovePending(self, request, user):
    #get user profile entity
    user_email = user.email()
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Profile not found')
    
    #get event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')

    #check that user is event organizer
    if user_email != event_entity.e_organizer:
      raise endpoints.UnauthorizedException('User must be event organizer')

    #if attendees is at capacity, return error
    if event_entity.capacity:
      if event_entity.num_attendees >= event_entity.capacity:
        raise endpoints.BadRequestException('Event is already at capacity')

    #get event roster entity
    e_roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not e_roster_entity:
      raise endpoints.NotFoundException('Event roster not found')

    #get event updates entity
    e_updates_entity = E_Updates.query(ancestor=event_entity.key).get()
    if not e_updates_entity:
      raise endpoints.NotFoundException('Event updates not found')

    #approve member while checking for capacity
    for attendee in getattr(request, 'approve_list'):
      if attendee in e_roster_entity.pending_attendees:
        if event_entity.capacity:
          if event_entity.num_attendees < event_entity.capacity:
            attendee_entity = ndb.Key(Profile, attendee).get()
            if attendee_entity:
              e_roster_entity.pending_attendees.remove(attendee)
              e_roster_entity.attendees.append(attendee)
              event_entity.num_pending_attendees-=1
              event_entity.num_attendees+=1

              update =  attendee_entity.first_name+' '+attendee_entity.last_name+' has joined'
              self._modUpdates(update, e_updates_entity)
        else:
          raise endpoints.BadRequestException('Event does not have capacity for all requested attendee approvals')
    
    e_updates_entity.put()
    e_roster_entity.put()
    event_entity.put()
    
    return EmptyResponse()

  """
  #***HELPER FUNCTION: APPROVE PENDING TEAMS FOR EVENT***
  #Description: approve pending teams for event (only event organizer)
  #Params: request- PUT request sent to eventApprovePendingTeam() endpoint (url safe original event name, event creator email, list of approvals)
  #Returns: empty
  #Called by: eventApprovePendingTeam() endpoint
  @ndb.transactional(xg=True)
  def _eApprovePendingTeams(self, request, user):
    #get user profile entity
    user_email = user.email()
    profile_entity = ndb.Key(Profile, user_email).get()
    if not profile_entity:
      raise endpoints.NotFoundException('Profile not found')
    
    #get event entity
    e_organizer = request.e_organizer_email
    e_title = request.url_event_orig_name
    e_title = e_title.replace(" ", "+")
    e_id = e_organizer + '_' + e_title
    event_entity = ndb.Key(Event, e_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')

    #check that user is event organizer
    if user_email != event_entity.e_organizer:
      raise endpoints.UnauthorizedException('User must be event organizer')
    
    #get event roster entity
    e_roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    if not e_roster_entity:
      raise endpoints.NotFoundException('Event roster not found')

    #get event updates entity
    e_updates_entity = E_Updates.query(ancestor=event_entity.key).get()
    if not e_updates_entity:
      raise endpoints.NotFoundException('Event updates not found')
    
    #for each team in the approval list
    for t_name in getattr(request, 'approve_list'):
      #get team entity
      t_name = t_name.replace(" ", "+")
      this_team_entity = ndb.Key(Team, t_name).get()
      if this_team_entity:
        #get capacity of team members
        t_cap = this_team_entity.t_capacity
        #get capacity of event
        e_cap = event_entity.capacity
        #get current number of attendees of event
        e_attendees = event_entity.num_attendees
        #ensure that event has room for entire team capacity
        if (e_attendees + t_cap) < e_cap:
          #save room for team in event by increasing number of attendants by team cap
          event_entity.num_attendees += t_cap
          #reflect changes for pending teams num and teams num (in event)
          event_entity.num_teams += 1
          event_entity.num_pending_teams -= 1
          #remove event from pending and add to active (in team)
          this_team_entity.pending_events.remove(e_id)
          this_team_entity.registered_events.append(e_id)
          #remove team from pending and add to active (in event)
          e_roster_entity.pending_teams.remove(this_team_entity.t_orig_name)
          e_roster_entity.teams.append(this_team_entity.t_orig_name)
          #create update
          update = this_team_entity.t_name+' has joined'
          self._modUpdates(update, e_updates_entity)
          #save team entity
          this_team_entity.put()
          #get team roster entity
          team_roster_entity = T_Roster.query(ancestor=this_team_entity.key).get()
          if team_roster_entity:
            #add team to event roster
            e_roster_entity.teams.append(this_team_entity.t_orig_name)
            #add team members to event roster
            if team_roster_entity.members:
              for member in team_roster_entity.members:
                e_roster_entity.attendees.append(member)
    
    #save event, event roster, and event updates
    e_updates_entity.put()
    e_roster_entity.put()
    event_entity.put()

    return EmptyResponse()
  """
  #***HELPER FUNCTION: REMOVE EVENT***
  #Description: remove a event entity if it exists
  #Params: request- DELETE request query string sent to deleteEvent() endpoint (url safe original event name, event creator email)
  #Returns: name of deleted event
  #Called by: deleteEvent() endpoint
  @ndb.transactional(xg=True)
  def _removeEvent(self, request, user):
    #get profile of logged in user
    decoded_email = user.email()
    #decoded_email = urllib.unquote(str(decoded_email)).decode("utf-8")
    profile_entity = ndb.Key(Profile, decoded_email).get()
    #get event entity of event to be deleted
    decoded_organizer_email = decoded_email
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    #decoded_organizer_email = urllib.unquote(str(decoded_organizer_email)).decode("utf-8")
    event_id = decoded_organizer_email + '_'+ decoded_name
    event_entity = ndb.Key(Event, event_id).get()
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')
    if event_entity.e_organizer != profile_entity.email:
      raise endpoints.UnauthorizedException('Authorization required')
    event_title = event_entity.e_title

    #get roster child of event entity
    roster_entity = E_Roster.query(ancestor=event_entity.key).get()
    #if there is a roster for the event, delete it
    if roster_entity:
      roster_entity.key.delete()

    #get e_updates child entity of event entity
    updates_entity = E_Updates.query(ancestor=event_entity.key).get()
    #if there is an updates entity for the event, delete it
    if updates_entity:
      updates_entity.key.delete()

    #delete the event
    event_entity.key.delete()
  
    return EmptyResponse()
  

  #***HELPER FUNCTION: GET EVENTS IN RADIUS***
  #Description: retrieve list of event IDs and distances for events within user radius (at most 20)
  #Params: request- GET request url portion sent to getEventsInRadius() endpoint (email, password)
  #Returns: list of events IDs and corresponding list of distances
  #Called by: getEventsInRadius() endpoint
  def _getRadiusEvents(self, request,user):
    prof_entity = ndb.Key(Profile, user.email()).get()
    user_lat = prof_entity.location.lat
    user_lon = prof_entity.location.lon

    #get 100 events
    #implement filter by state here when more users happen
    event_query = Event.query()
    events = event_query.fetch(100)

    # ONLY 25 ORIGINS OR DESTINATIONS PER DISTANCE MATRIX REQUEST
    num_events = len(events)
    matrixed_events = 0
    total_matrixed_events = 0
    large_result_list = []
    origins = []
    origins.append([user_lat, user_lon])
    destinations = []
   
    for event in events:
      if matrixed_events < 25 and total_matrixed_events != num_events-1:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1
      else:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1

        matrix_result = gmaps.distance_matrix(origins, destinations, mode="driving",
                                            language="en",
                                            units="imperial")
        this_result = matrix_result['rows'][0]['elements']
        for result in this_result:
          large_result_list.append(result)
        matrixed_events = 0
        destinations = []
        this_result = []

    response = GetEventsInRadiusResponse()
    event_index_list = []
    distance_list = []
    count=0
    response_count = 0
    #get up to 50 events that are in radius set by user
    for result in large_result_list:
      if response_count >= 50:
        break
      if result['distance']['value'] <= (prof_entity.search_rad * 1609.34):
        #vent_list.append(events[count])
        event_index_list.append(count)
        distance_list.append(result['distance']['value'])
        response_count += 1
      count += 1
    #sort events in user radius
    response_dict = dict(zip(event_index_list, distance_list))
    sorted_index_list = []
    new_distance_list = []
    for key, value in sorted(response_dict.iteritems(), key=lambda (k,v): (v,k)):
      sorted_index_list.append(key)
      new_distance_list.append(value)
    
    #get events within user radius that also have matching tags
    break_check = 0
    final_count = 0
    d_pop_count = -1
    events_matching_tags_radius = []
    for this_index in sorted_index_list:
      d_pop_count += 1
      if final_count >= 20:
        break
      if break_check == 1:
        break_check = 0
      for tag in events[this_index].interests:
        if break_check == 1:
          break
        for interest in prof_entity.interests:
          if tag == interest:
            events_matching_tags_radius.append(events[this_index])
            response.distances.append(new_distance_list[d_pop_count]/1609.34)
            final_count += 1
            break_check =1
            break

    #if set of matching events within radius is not big enough,
    #put events in set that are in radius but do not match tags
    final_count2 = 0
    if final_count < 20:
      for this_event_index in sorted_index_list:
        if final_count >= 20:
          break
        if events[this_event_index] not in events_matching_tags_radius:
          events_matching_tags_radius.append(events[this_event_index])
          response.distances.append(new_distance_list[final_count2] / 1609.34)
          final_count += 1
        final_count2 += 1
    
    #set response string list to IDs of matched/in radius events
    for final_event in events_matching_tags_radius:
      response.events.append(final_event.e_organizer + '/' + final_event.e_orig_title)

    return response


  #***HELPER FUNCTION: GET EVENTS IN RADIUS BY DATE***
  #Description: retrieve list of event IDs for events within user radius (at most 50)
  #Params: request- GET request url portion sent to getEventsInRadiusByDate() endpoint (email, password)
  #Returns: list of events IDs sorted by date
  #Called by: getEventsInRadiusByDate() endpoint
  def _getRadiusEventsByDate(self, request,user):
    prof_entity = ndb.Key(Profile, user.email()).get()
    user_lat = prof_entity.location.lat
    user_lon = prof_entity.location.lon

    #get 100 events
    #implement filter by state here when more users happen
    event_query = Event.query()
    events = event_query.fetch(100)

    # ONLY 25 ORIGINS OR DESTINATIONS PER DISTANCE MATRIX REQUEST
    num_events = len(events)
    matrixed_events = 0
    total_matrixed_events = 0
    large_result_list = []
    origins = []
    origins.append([user_lat, user_lon])
    destinations = []
   
    for event in events:
      if matrixed_events < 25 and total_matrixed_events != num_events-1:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1
      else:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1

        matrix_result = gmaps.distance_matrix(origins, destinations, mode="driving",
                                            language="en",
                                            units="imperial")
        this_result = matrix_result['rows'][0]['elements']
        for result in this_result:
          large_result_list.append(result)
        matrixed_events = 0
        destinations = []
        this_result = []

    response = GetEventsInRadiusByDateResponse()
    event_index_list = []
    date_list = []
    count=0
    response_count = 0
    #get up to 50 events that are in radius set by user
    for result in large_result_list:
      if response_count >= 50:
        break
      if result['distance']['value'] <= (prof_entity.search_rad * 1609.34):
        event_index_list.append(count)
        date_list.append(events[count].sched[0].date_start)
        response_count += 1
      count += 1

    #sort events in user radius
    response_dict = dict(zip(event_index_list, date_list))
    sorted_index_list = []
    sorted_date_list = []
    for key, value in sorted(response_dict.iteritems(), key=lambda (k,v): (v,k)):
      sorted_index_list.append(key)
      sorted_date_list.append(value)
    
    
    for index in sorted_index_list:
      response.events.append(events[index].e_organizer+'_'+events[index].e_orig_title)

    return response
    

  #***HELPER FUNCTION: ADD LEADERS TO EVENT***
  #Description: add leaders to an event (creating a Roster child entity if not created already) and event to leaders
  #Params: request- POST request sent to addEventLeaders() endpoint (leaders emails)
  #Returns: request- POST request sent to addEventLeaders() endpoint (leaders emails)
  #Called by: addEventLeaders() endpoint
  @ndb.transactional(xg=True)
  def _addLeaders(self, request, user):
    #get user profile entity
    profile_entity = ndb.Key(Profile, user.email()).get()
    #get event entity
    decoded_organizer_email = user.email()
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    event_id = decoded_organizer_email +'_'+ decoded_name

    event_entity = ndb.Key(Event, event_id).get()
    #if event does not exist, raise exception
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')
    else:
      #check that caller is organizer of event
      if event_entity.e_organizer != profile_entity.email:
        raise endpoints.UnauthorizedException('Authorization required')
      #check if event already has Roster entity
      roster_entity = E_Roster.query(ancestor=event_entity.key).get()
      if roster_entity:
        #add each leader passed in HTTP request
        check = 0
        for new_leader in getattr(request,'leaders'):
          for old_leader in roster_entity.leaders:
            if new_leader == old_leader or new_leader == event_entity.e_organizer:
              check = 1
        if check == 1:
          raise endpoints.BadRequestException('Cannot add existing leaders')
        else:
          roster_entity.leaders += getattr(request, 'leaders')
      roster_entity.put()
    
    return EmptyResponse()
  

  #***HELPER FUNCTION: DELETE LEADERS FROM EVENT***
  #Description: remove leaders from an event and event from leaders profile
  #Params: request- DELETE url query string sent to deleteEventLeaders() endpoint (leaders emails)
  #Returns: request- DELETE url query string sent to deleteEventLeaders() endpoint (leaders emails)
  #Called by: deleteEventLeaders() endpoint
  @ndb.transactional(xg=True)
  def _deleteLeaders(self, request, user):
    #get user profile entity
    decoded_email = user.email()
    #decoded_email = urllib.unquote(str(decoded_email)).decode("utf-8")
    profile_entity = ndb.Key(Profile, decoded_email).get()
    #get event entity
    decoded_organizer_email = decoded_email
    #decoded_organizer_email = urllib.unquote(str(decoded_organizer_email)).decode("utf-8")
    decoded_name = request.url_event_orig_name
    decoded_name = decoded_name.replace(" ", "+")
    event_id = decoded_organizer_email +'_'+ decoded_name
    event_entity = ndb.Key(Event, event_id).get()
    #if event does not exist, raise exception
    if not event_entity:
      raise endpoints.NotFoundException('Event not found')
    else:
      #check that caller is organizer of event
      if event_entity.e_organizer != profile_entity.email:
        raise endpoints.UnauthorizedException('Authorization required')
      #check if event already has Roster entity
      roster_entity = E_Roster.query(ancestor=event_entity.key).get()
      if roster_entity:
        #remove each leader passed in HTTP request
        for remove_leader in getattr(request,'leaders'):
          for old_leader in roster_entity.leaders:
            if remove_leader == old_leader:
              roster_entity.leaders.remove(remove_leader)
      roster_entity.put()

    return EmptyResponse()
  
  #***HELPER FUNCTION: SEARCH FOR EVENTS BY INTEREST/SKILL KEYWORD OR EVENT TITLE***
  #Description: searches for (within user radius) events with keyword in title (adds up to 10) then searches for events with
  #             keyword in interests or skills tags (adds up to 10 more) and returns list of titles and ids
  #Params: request- GET url query string sent to searchEvent() endpoint (search term)
  #Returns: request- list of matching event titles and event ids
  #Called by: searchEvent() endpoint
  def _mainSearchEvent(self, request, user):
    #get user profile entity
    profile_entity = ndb.Key(Profile, user.email()).get()
    if not profile_entity:
      raise endpoints.NotFoundException('User profile not found')
    user_lat = profile_entity.location.lat
    user_lon = profile_entity.location.lon
    #get user search radius
    search_rad = profile_entity.search_rad
    
    #get list of separated search terms
    search_terms = request.search_term
    search_terms = search_terms.split()

    if len(search_terms) > 5:
      raise endpoints.BadRequestException("Cannot have more than 5 search terms")

    #iterate for each search term
    large_event_list = []
    for term in search_terms:
      #add all events whose name matches search term to list (at most 50)
      event_title_query = Event.query(Event.e_title_index == term)
      events_title = event_title_query.fetch(50)
      for event in events_title:
        if event not in large_event_list:
          large_event_list.append(event)
      
      #add all events whose interests match search term to list (at most 50)
      event_int_query = Event.query(Event.interests == term)
      events_int = event_int_query.fetch(50)
      for event in events_int:
        if event not in large_event_list:
          large_event_list.append(event)

      #add all events whose skills match search term to list (at most 50)
      event_skills_query = Event.query(Event.req_skills == term)
      events_skills = event_skills_query.fetch(50)
      for event in events_skills:
        if event not in large_event_list:
          large_event_list.append(event)

    # ONLY 25 ORIGINS OR DESTINATIONS PER DISTANCE MATRIX REQUEST
    num_events = len(large_event_list)
    matrixed_events = 0
    total_matrixed_events = 0
    large_result_list = []
    origins = []
    origins.append([user_lat, user_lon])
    destinations = []
   
    for event in large_event_list:
      if matrixed_events < 25 and total_matrixed_events != num_events-1:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1
      else:
        destinations.append([event.e_location.lat, event.e_location.lon])
        matrixed_events += 1
        total_matrixed_events += 1

        matrix_result = gmaps.distance_matrix(origins, destinations, mode="driving",
                                            language="en",
                                            units="imperial")
        this_result = matrix_result['rows'][0]['elements']
        for result in this_result:
          large_result_list.append(result)
        matrixed_events = 0
        destinations = []
        this_result = []

    event_index_list = []
    distance_list = []
    count=0
    response_count = 0
    #get up to 50 events that are in radius set by user
    for result in large_result_list: 
      if response_count >= 50:
        break
      if result['distance']['value'] <= (profile_entity.search_rad * 1609.34):
        #vent_list.append(events[count])
        event_index_list.append(count)
        distance_list.append(result['distance']['value'])
        response_count += 1
      count += 1

    #sort events in user radius
    response_dict = dict(zip(event_index_list, distance_list))
    sorted_index_list = []
    new_distance_list = []
    for key, value in sorted(response_dict.iteritems(), key=lambda (k,v): (v,k)):
      sorted_index_list.append(key)
      new_distance_list.append(value)

    response = EventSearchResponse()
    
    #return up to 20 results
    final_num_events = len(new_distance_list)
    final_count = 0
    for x in range(final_num_events):
      if final_count >= 20:
        break
      response.event_titles.append(large_event_list[sorted_index_list[x]].e_title)
      response.event_ids.append(large_event_list[sorted_index_list[x]].e_organizer + '_' +large_event_list[sorted_index_list[x]].e_title)
      response.distances.append(new_distance_list[x] / 1609.34)
      final_count += 1
    
    return response

##################################################################################
##################           ENDPOINT FUNCTIONS             ######################
##################################################################################
  
  #****ENDPOINT: NEW PROFILE CREATION***
  #-accepts: profile info
  #-returns: profile info
  @endpoints.method(ProfileCreateForm, EmptyResponse, 
  path='profiles', http_method='POST', name='createProfile')
  def createProfile(self, request):
    user = self._authenticateUser()
    return self._uploadNewProfile(request,user)

  #****ENDPOINT: GET PROFILE***
  #-accepts: email to which profile is associated with
  #-returns: all profile core info
  @endpoints.method(PROF_GET_REQUEST, ProfileGetResponse, 
  path='profiles/{email_to_get}', http_method='GET', name='getProfile')
  def getProfile(self, request):
    user = self._authenticateUser()
    return self._viewProfile(request, user)

  #****ENDPOINT: GET PROFILE EVENTS***
  #-accepts: email to which profile is associated with
  #-returns: all registered events, attended events, and created events for profile
  @endpoints.method(PROF_GET_REQUEST, GetProfileEvents, 
  path='profiles/{email_to_get}/events', http_method='GET', name='getProfileEvents')
  def getProfileEvents(self, request):
    user = self._authenticateUser()
    return self._viewProfileEvents(request, user)

  #****ENDPOINT: GET PROFILE TEAMS***
  #-accepts: email to which profile is associated with
  #-returns: all registered teams
  @endpoints.method(PROF_GET_REQUEST, GetProfileTeamsResponse, 
  path='profiles/{email_to_get}/teams', http_method='GET', name='getProfileTeams')
  def getProfileTeams(self, request):
    user = self._authenticateUser()
    return self._viewProfileTeams(request, user)

  #****ENDPOINT: EDIT PROFILE***
  #-accepts: LoginForm (email, password)
  #-returns: user email
  @endpoints.method(ProfileEditForm, EmptyResponse, 
  path='profiles', http_method='PUT', name='editProfile')
  def editProfile(self, request):
    user = self._authenticateUser()
    return self._editExistingProfile(request, user)

  #****ENDPOINT: DELETE PROFILE***
  #-accepts: user email (which is the Profile entity key name)
  #-returns: user email of deleted profile
  @endpoints.method(EMPTY_REQUEST, EmptyResponse, 
  path='profiles', http_method='DELETE', name='deleteProfile')
  def deleteProfile(self, request):
    user = self._authenticateUser()
    return self._removeProfile(request, user)

  #****ENDPOINT: CREATE EVENT***
  #-accepts: user email (which is the Profile entity key name)
  #-returns: user email of deleted profile
  @endpoints.method(EventCreateForm, EmptyResponse, 
  path='events', http_method='POST', name='createEvent')
  def createEvent(self, request):
    user = self._authenticateUser()
    return self._createEvent(request, user)

  #****ENDPOINT: GET EVENT***
  #-accepts: event organizer email, original event name (url-safe)
  #-returns: all event core info
  @endpoints.method(EVENT_DEL_REQUEST, EventGetResponse, 
  path='events/{e_organizer_email}/{url_event_orig_name}', http_method='GET', name='getEvent')
  def getEvent(self, request):
    self._authenticateUser()
    return self._viewEvent(request)

  #****ENDPOINT: GET EVENT ROSTER***
  #-accepts: event organizer email, original event name (url-safe)
  #-returns: event roster info
  @endpoints.method(EVENT_DEL_REQUEST, EventRosterGetResponse, 
  path='events/{e_organizer_email}/{url_event_orig_name}/roster', http_method='GET', name='getEventRoster')
  def getEventRoster(self, request):
    self._authenticateUser()
    return self._viewEventRoster(request)

  #****ENDPOINT: GET EVENT UPDATES***
  #-accepts: event organizer email, original event name (url-safe)
  #-returns: event updates and update date/times
  @endpoints.method(EVENT_DEL_REQUEST, EventUpdatesGetResponse, 
  path='events/{e_organizer_email}/{url_event_orig_name}/updates', http_method='GET', name='getEventUpdates')
  def getEventUpdates(self, request):
    self._authenticateUser()
    return self._viewEventUpdates(request)

  #****ENDPOINT: GET EVENTS IN RADIUS***
  #-accepts: email and password
  #-returns: list of 20 closest events
  @endpoints.method(PROF_DEL_REQUEST, GetEventsInRadiusResponse, 
  path='events/prefill', http_method='GET', name='getEventsInRadius')
  def getEventsInRadius(self, request):
    user = self._authenticateUser()
    return self._getRadiusEvents(request,user)

  #****ENDPOINT: GET EVENTS IN RADIUS SORTED BY DATE***
  #-accepts: email and password
  #-returns: list of 50 closest events
  @endpoints.method(PROF_DEL_REQUEST, GetEventsInRadiusByDateResponse, 
  path='events/prefill/dates', http_method='GET', name='getEventsInRadiusByDate')
  def getEventsInRadiusByDate(self, request):
    user = self._authenticateUser()
    return self._getRadiusEventsByDate(request,user)
  
  #****ENDPOINT: EDIT EVENT***
  #-accepts: user email (which is the Profile entity key name)
  #-returns: user email of deleted profile
  @endpoints.method(EventEditForm, EmptyResponse,
  path='events', http_method='PUT', name='editEvent')
  def editEvent(self, request):
    user = self._authenticateUser()
    return self._editExistingEvent(request, user)
    
  #****ENDPOINT: DELETE EVENT***
  #-accepts: original event name, event creator email
  #-returns: name of deleted event
  @endpoints.method(EVENT_DEL_REQUEST, EmptyResponse, 
  path='events/{url_event_orig_name}', http_method='DELETE', name='deleteEvent')
  def deleteEvent(self, request):
    user = self._authenticateUser()
    return self._removeEvent(request, user)

  #****ENDPOINT: ADD EVENT LEADERS***
  #-accepts: leaders to add, original event name, user email, user password
  #-returns: leaders to add, original event name, user email, user password
  @endpoints.method(EVENT_ADD_LEADERS_REQUEST, EmptyResponse,
  path='events/{url_event_orig_name}/leaders', http_method='PUT', name='addEventLeaders')
  def addEventLeaders(self, request):
    user = self._authenticateUser()
    return self._addLeaders(request, user)

  #****ENDPOINT: DELETE EVENT LEADERS***
  #-accepts: leaders to delete, original event name, user email, user password
  #-returns: leaders to delete, original event name, user email, user password
  @endpoints.method(EVENT_DELETE_LEADERS_REQUEST, EmptyResponse,
  path='events/{url_event_orig_name}/leaders', http_method='DELETE', name='deleteEventLeaders')
  def deleteEventLeaders(self, request):
    user = self._authenticateUser()
    return self._deleteLeaders(request, user)

  #****ENDPOINT: CREATE NEW TEAM***
  #-accepts: TeamCreateForm (team info)
  #-returns: team info
  @endpoints.method(TeamCreateForm, EmptyResponse, 
  path='teams', http_method='POST', name='createTeam')
  def createTeam(self, request):
    user = self._authenticateUser()
    return self._uploadNewTeam(request, user)

  #****ENDPOINT: EDIT TEAM***
  #-accepts: original team name, team info to change
  #-returns: original team name, team info to change
  @endpoints.method(TeamEditForm, EmptyResponse,
  path='teams', http_method='PUT', name='editTeam')
  def editTeam(self, request):
    user = self._authenticateUser()
    return self._editExistingTeam(request, user)

  #****ENDPOINT: DELETE TEAM***
  #-accepts: original team name
  #-returns: name of deleted team
  @endpoints.method(TEAM_DEL_REQUEST, EmptyResponse, 
  path='teams/{url_team_orig_name}', http_method='DELETE', name='deleteTeam')
  def deleteTeam(self, request):
    user = self._authenticateUser()
    return self._removeTeam(request, user)

  #****ENDPOINT: GET TEAM***
  #-accepts: original team name
  #-returns: all team info
  @endpoints.method(TEAM_DEL_REQUEST, TeamGetResponse, 
  path='teams/{url_team_orig_name}', http_method='GET', name='getTeam')
  def getTeam(self, request):
    self._authenticateUser()
    return self._viewTeam(request)

  #****ENDPOINT: GET TEAM ROSTER***
  #-accepts: original team name (url-safe)
  #-returns: team roster info
  @endpoints.method(TEAM_DEL_REQUEST, TeamRosterGetResponse, 
  path='teams/{url_team_orig_name}/roster', http_method='GET', name='getTeamRoster')
  def getTeamRoster(self, request):
    self._authenticateUser()
    return self._viewTeamRoster(request)
  """
  #****ENDPOINT: REGISTER TEAM FOR EVENT***
  #-accepts: event name to sign up for, event organizer email
  #-returns: event signed up for
  @endpoints.method(TEAM_EVENT_REG_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/registration/team', http_method='PUT', name='registerTeamForEvent')
  def registerTeamForEvent(self, request):
    user = self._authenticateUser()
    return self._signUpTeamEvent(request, user)
  
  #****ENDPOINT: DEREGISTER TEAM FROM EVENT***
  #-accepts: event name to sign out of, event organizer email
  #-returns: event signed out of
  @endpoints.method(TEAM_EVENT_DEREG_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/registration/team', http_method='DELETE', name='deregisterTeamFromEvent')
  def deregisterTeamFromEvent(self, request):
    user = self._authenticateUser()
    return self._signOutTeamEvent(request, user)
  """
  #****ENDPOINT: REGISTER USER FOR EVENT***
  #-accepts: event name to sign up for, event organizer email
  #-returns: event signed up for
  @endpoints.method(REGISTER_EVENT_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/registration', http_method='PUT', name='registerForEvent')
  def RegisterForEvent(self, request):
    user = self._authenticateUser()
    return self._signUpEvent(request, user)
  
  #****ENDPOINT: DEREGISTER USER FOR EVENT***
  #-accepts: event name to sign up for, event organizer email
  #-returns: event signed up for
  @endpoints.method(EVENT_DEL_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/registration', http_method='DELETE', name='deregisterForEvent')
  def deregisterForEvent(self, request):
    user = self._authenticateUser()
    return self._signOutEvent(request, user)

  #****ENDPOINT: REGISTER USER FOR TEAM***
  #-accepts: original team name to sign up for (team name is unique)
  #-returns: team name signed up for
  @endpoints.method(TEAM_DEL_REQUEST, EmptyResponse,
  path='teams/{url_team_orig_name}/registration', http_method='PUT', name='registerForTeam')
  def RegisterForTeam(self, request):
    user = self._authenticateUser()
    return self._signUpTeam(request,user)

  #****ENDPOINT: DEREGISTER USER FOR TEAM***
  #-accepts: team name to signup for
  #-returns: team signed up for
  @endpoints.method(TEAM_DEL_REQUEST, EmptyResponse,
  path='teams/{url_team_orig_name}/registration', http_method='DELETE', name='deregisterForTeam')
  def deregisterForTeam(self, request):
    user = self._authenticateUser()
    return self._signOutTeam(request, user)

  #****ENDPOINT: QR EVENT USER SIGN IN***
  #-accepts: event name to qr sign up for, event organizer email
  #-returns: event qr signed in to
  @endpoints.method(QR_SIGNIN_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/qr', http_method='PUT', name='qrSignInEvent')
  def qrSignInEvent(self, request):
    user = self._authenticateUser()
    return self._qrInEvent(request, user)

  #****ENDPOINT: QR EVENT USER SIGN OUT***
  #-accepts: event name to qr sign out of for, event organizer email
  #-returns: event qr signed in to
  @endpoints.method(EVENT_DEL_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/qr', http_method='DELETE', name='qrSignOutEvent')
  def qrSignOutEvent(self, request):
    user = self._authenticateUser()
    return self._qrOutEvent(request, user)

  #****ENDPOINT: EVENT SEARCH***
  #-accepts: keyword/event name to search events for
  #-returns: list of names and list of event ids
  @endpoints.method(EVENT_SEARCH_REQUEST, EventSearchResponse,
  path='events/search', http_method='GET', name='searchEvent')
  def searchEvent(self, request):
    user = self._authenticateUser()
    return self._mainSearchEvent(request, user)
  
  #****ENDPOINT: APPROVE PENDING EVENT ATTENDEES***
  #-accepts: event name, event organizer email
  #-returns: event name
  @endpoints.method(EVENT_APPROVE_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/approve', http_method='PUT', name='eventApprovePending')
  def eventApprovePending(self, request):
    user = self._authenticateUser()
    return self._eApprovePending(request, user)

  #****ENDPOINT: APPROVE PENDING TEAM MEMBERS***
  #-accepts: list of approvals (emails), team name
  #-returns: list of approvals
  @endpoints.method(APPROVE_TEAM_MEMBERS_REQUEST, EmptyResponse,
  path='teams/{team_name}/approve', http_method='PUT', name='teamApprovePending')
  def teamApprovePending(self, request):
    user = self._authenticateUser()
    return self._tApprovePending(request, user)
  
  """
  #****ENDPOINT: APPROVE PENDING TEAMS FOR EVENT***
  #-accepts: list of approvals (team names), event organizer email, event original name
  #-returns: empty
  @endpoints.method(APPROVE_PENDING_TEAMS_REQUEST, EmptyResponse,
  path='events/{e_organizer_email}/{url_event_orig_name}/approveteam', http_method='PUT', name='eventApprovePendingTeams')
  def eventApprovePendingTeams(self, request):
    user = self._authenticateUser()
    return self._eApprovePendingTeams(request, user)
  """
  """
  #****ENDPOINT: clean events debugger***
  @endpoints.method(EMPTY_REQUEST, EmptyResponse,
  path='debug', http_method='GET', name='debug')
  def debug(self, request):
    return self._eventsCleanPast()

  #****ENDPOINT: clean events debugger***
  @endpoints.method(EMPTY_REQUEST, EmptyResponse,
  path='debug2', http_method='GET', name='debug2')
  def debug2(self, request):
    return self._eventsDistributeRemainingHours()
  """

  ##################################################################################
  ##################           STATIC FUNCTIONS               ######################
  ##################################################################################

  
  #***STATIC FUNCTION: CRON JOB FOR CLEANING EVENTS***
  #Description: called by cron job every 2 hours to clean events (ie. delete past events and convert to history events)
  @staticmethod
  def _eventsCleanPast():
    event_list = Event.query().fetch()
    now = datetime.now()

    if event_list:
      for event in event_list:
        if event.discard_flag >= len(event.sched):
          num_days = len(event.sched)
          last_day = event.sched[num_days-1]
          if last_day.date_end < now:
            #get event roster object
            roster_object = E_Roster.query(ancestor=event.key).get()
            #get updates object
            updates_entity = E_Updates.query(ancestor=event.key).get()

            #CALCULATE AVERAGE USER HOURS HERE#####
            hours = 0
            if roster_object.total_hours == 0:
              hours = 0
            elif roster_object.total_sign_in > 0:
              hours = roster_object.total_hours/roster_object.total_sign_in
            #######################################
            event_history = EventHistory(
              e_title = event.e_title,
              e_orig_title = event.e_orig_title,
              e_title_index = event.e_title_index,
              e_organizer = event.e_organizer,
              sched = event.sched,
              street = event.street,
              city = event.city,
              state = event.state,
              funds_raised = event.funds_raised,
              average_att_hours = hours
            )
            if hasattr(roster_object, 'attendees'):
              event_history.registered_attendees = roster_object.attendees
            if hasattr(roster_object, 'signed_in_attendees'):
              event_history.signed_in_attendees = roster_object.signed_in_attendees
            event_history.put()
            event.key.delete()
            updates_entity.key.delete()
            roster_object.key.delete()
    
    return EmptyResponse()

  #***STATIC FUNCTION: CRON JOB FOR DISTRIBUTING HOURS TO EVENT ATTENDEES***
  #Description: called by cron job every 2 hours to distribute hours and set discard flag to 1 
  @staticmethod
  def _eventsDistributeRemainingHours():
    event_list = Event.query().fetch()
    now = datetime.now()

    if event_list:
      #for each event
      for event in event_list:
        #get number of days of the event
        num_days = len(event.sched)
        #if there are days whose hours have not beet distributed by default yet
        if event.discard_flag < num_days:
          #for days whose hours have not been distributed by default yet
          for x in range(event.discard_flag, num_days):
            #if the end date for this day of the event has passed
            if event.sched[x].date_end < now:
              #get event roster
              roster_entity = E_Roster.query(ancestor=event.key).get()
              if hasattr(roster_entity, 'signed_in_attendees'):
                count = 0
                #for each signed in attendee
                for this_attendee in roster_entity.signed_in_attendees:
                  #if the attendee has not already signed out
                  if this_attendee not in roster_entity.signed_out_attendees:
                    #calculate time spent for that attendee
                    elapsed = event.sched[x].date_end - roster_entity.sign_in_times[count]
                    hours = float(elapsed.seconds)/3600
                    hours = round(hours,2)
                    #add to total hours of event
                    roster_entity.total_hours += hours
                    #get profile entity of attendee
                    this_profile = ndb.Key(Profile, this_attendee).get()
                    if this_profile:
                      #add the event to the users completed events
                      event_string = event.e_organizer + '_' + event.e_orig_title
                      this_profile.attended_events.remove(event_string)
                      this_profile.completed_events.append(event_string)
                      #add the hours spent at this event to event hours
                      this_profile.event_hours.append(hours)
                      #add to the attendees total hours
                      if this_profile.hours:
                        this_profile.hours += hours
                      else:
                        this_profile.hours = hours
                      this_profile.put()
                  count += 1
              del roster_entity.sign_in_times[:]
              del roster_entity.sign_out_times[:]
              del roster_entity.signed_in_attendees[:]
              del roster_entity.signed_out_attendees[:]
              event.discard_flag += 1
              roster_entity.put()
        event.put()
  
    return EmptyResponse()


  
api = endpoints.api_server([connectEDApi])