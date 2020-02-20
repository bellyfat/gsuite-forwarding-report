# I created this class to encapsulate all the peices needed for authentication and hopefully
# avoid any overhead in re-authenticating or having to keep track of the various objects
# neccessary for authentication

import config
import os

import oauth2client.client
import oauth2client.file
import oauth2client.tools
import apiclient
import apiclient.discovery
import apiclient.errors
import apiclient.http
import httplib2

import pprint

from oauth2client.service_account import ServiceAccountCredentials

class Auth:

	def __init__(self, scopes=None, authdir=None, verbose=False):
		if authdir is None:
			authdir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'oauth2')
		self.oauth2file = os.path.join(authdir,'oauth2.txt')
		self.CLIENT_SECRETS = os.path.join(authdir,'client_secrets.json')
#		self.OAUTH2SERVICEJSON = os.path.join(authdir,'oauth2service.json')
		self.credentials = None
		self.http = httplib2.Http()
		self.CUSTOMER_ID = config.CUSTOMER_ID
		self.verbose = verbose

		if scopes == 'ro':
			self.possible_scopes = [u'https://www.googleapis.com/auth/admin.directory.user',
							   u'https://www.googleapis.com/auth/admin.directory.group',
							   u'https://www.googleapis.com/auth/admin.directory.group.member',
							   u'https://www.googleapis.com/auth/calendar',
							   u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',
							   u'https://www.googleapis.com/auth/apps.groups.settings',
							   u'https://www.googleapis.com/auth/admin.directory.user.security',
							   u'https://www.googleapis.com/auth/admin.directory.orgunit.readonly',
							   u'https://www.googleapis.com/auth/admin.reports.usage.readonly']
							   #u'https://www.googleapis.com/auth/admin.directory.user.security.readonly',
								#u'https://www.googleapis.com/auth/apps.groups.settings.readonly',
							#	u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/#readonly'

		if scopes == 'all' or scopes is None:
			self.possible_scopes = [u'https://www.googleapis.com/auth/admin.directory.group',            # Groups Directory Scope
			                 u'https://www.googleapis.com/auth/admin.directory.orgunit',          # Organization Directory Scope
			                 u'https://www.googleapis.com/auth/admin.directory.user',             # Users Directory Scope
			                 u'https://www.googleapis.com/auth/admin.directory.device.chromeos',  # Chrome OS Devices Directory Scope
			                 u'https://www.googleapis.com/auth/admin.directory.device.mobile',    # Mobile Device Directory Scope
			                 u'https://apps-apis.google.com/a/feeds/emailsettings/2.0/',          # Email Settings API (DEPRECATED)
							 u'https://www.googleapis.com/auth/gmail.settings.basic',
							 u'https://www.googleapis.com/auth/gmail.settings.sharing',
			                 u'https://apps-apis.google.com/a/feeds/calendar/resource/',          # Calendar Resource API
			                 u'https://apps-apis.google.com/a/feeds/compliance/audit/',           # Email Audit API
			                 u'https://apps-apis.google.com/a/feeds/domain/',                     # Admin Settings API
			                 u'https://www.googleapis.com/auth/apps.groups.settings',             # Group Settings API
			                 u'https://www.googleapis.com/auth/calendar',                         # Calendar Data API
			                 u'https://www.googleapis.com/auth/admin.reports.audit.readonly',     # Audit Reports
			                 u'https://www.googleapis.com/auth/drive.file',                       # Drive API - Admin user access to files created or opened by the app
			                 u'https://www.googleapis.com/auth/apps.licensing',                   # License Manager API
			                 u'https://www.googleapis.com/auth/admin.directory.user.security',    # User Security Directory API
			                 u'https://www.googleapis.com/auth/admin.directory.notifications',    # Notifications Directory API
			                 u'https://www.googleapis.com/auth/siteverification',                 # Site Verification API
			                 u'https://mail.google.com/'] 										  #scopes = [u'email',]

		if type(scopes) == 'list':
			self.possible_scopes = scopes

	def load_auth(self):

		def doRequestOauth(CLIENT_SECRETS):

			class cmd_flags(object):
				def __init__(self):
					self.short_url = True
					self.noauth_local_webserver = False
					self.logging_level = u'ERROR'
					self.auth_host_name = u'localhost'
					self.auth_host_port = [8080, 9090]

			flags = cmd_flags()
			flags.noauth_local_webserver = True
			FLOW = oauth2client.client.flow_from_clientsecrets(self.CLIENT_SECRETS,scope=self.possible_scopes,message="")
			storage = oauth2client.file.Storage(self.oauth2file)
			self.credentials = storage.get()

			if self.credentials is None or self.credentials.invalid:
				self.credentials = oauth2client.tools.run_flow(flow=FLOW, storage=storage, flags=flags)


		storage = oauth2client.file.Storage(self.oauth2file)
		credentials = storage.get()

		if self.credentials is None or self.credentials.invalid:
			doRequestOauth(self.CLIENT_SECRETS)
			storage = oauth2client.file.Storage(self.oauth2file)
			self.credentials = storage.get()
		self.http = self.credentials.authorize(self.http)

		if self.credentials.invalid == False:
			return True
		return False


	def api_service(self, api_name, api_version):
		if self.credentials is None or self.credentials.invalid:
			self.load_auth()
		return apiclient.discovery.build(api_name, api_version, http=self.http)



class ServiceAuth:

	def __init__(self, scopes=None, authdir=None, verbose=False):
		if authdir is None:
			authdir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'oauth2')
		self.oauth2file = os.path.join(authdir,'oauth2.txt')
		self.CLIENT_SECRETS = os.path.join(authdir,'client_secrets.json')
		self.OAUTH2SERVICEJSON = os.path.join(authdir,'oauth2service.json')

		self.credentials = None
		self.http = httplib2.Http()
		self.CUSTOMER_ID = config.CUSTOMER_ID
		self.verbose = verbose

		if scopes == 'all' or scopes is None:
			self.possible_scopes = [u'https://www.googleapis.com/auth/gmail.settings.basic',
							 u'https://www.googleapis.com/auth/gmail.settings.sharing',]

		if type(scopes) == 'list':
			self.possible_scopes = scopes


	def load_auth(self, delegated=None):
		testscopes = [u'https://www.googleapis.com/auth/gmail.settings.basic',u'https://www.googleapis.com/auth/gmail.settings.sharing',]
		self.credentials = ServiceAccountCredentials.from_json_keyfile_name(self.OAUTH2SERVICEJSON, scopes=self.possible_scopes)

		if delegated is not None:
			self.credentials = self.credentials.create_delegated(delegated)
		#pprint.pprint(vars(self.credentials))
		self.http = self.credentials.authorize(self.http)


	def api_service(self, api_name, api_version):
		#if self.credentials is None or self.credentials.invalid:
		#pprint.pprint(vars(self.http.credentials))
		return apiclient.discovery.build(api_name, api_version, credentials=self.credentials)

