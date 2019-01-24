import webapp2
import httplib2
import datetime
from google.appengine.ext import ndb
import oauth2client.client
import googleapiclient.discovery
import pprint
import json

# From https://www.chromium.org/chromium-os/tpm_firmware_update
CROS_TPM_VULN_VERSIONS = [u'41f',  u'420', u'628', u'8520',]
CROS_TPM_FIXED_VERSIONS = [u'422', u'62b', u'8521',]

class RefreshTokens(ndb.Model):
  refresh_token = ndb.StringProperty(indexed=True)

class JsonHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    deviceid = self.request.get(argument_name='deviceid', default_value=None)
    fields = self.request.get(argument_name=u'fields', default_value=u'annotatedAssetId,annotatedLocation,annotatedUser,ethernetMacAddress,macAddress,model,notes,orgUnitPath,serialNumber,tpmVersionInfo/firmwareVersion')
    if not deviceid:
      self.response.out.write('{"success": false, "error_message": "Need to specify deviceid parameter"}')
      return
    primary_domain = self.request.get(argument_name='primary_domain', default_value=None)
    if not primary_domain:
      self.response.out.write('{"success": false, "error_message": "Need to specify primary_domain parameter"}')
      return
    token = RefreshTokens.get_by_id(id=primary_domain)
    if not token:
      self.response.out.write('{"success": false, "error_message": "Please login as an administrator and <a target=\"_blank\" href=\"adminlogin\">authorize this extension."}')
      return
    cs_data = json.loads(open('client_secrets.json').read())
    credentials = oauth2client.client.OAuth2Credentials(
     access_token='',
     client_id=cs_data['web']['client_id'],
     client_secret=cs_data['web']['client_secret'],
     refresh_token=token.refresh_token,
     token_expiry=datetime.datetime.today() - datetime.timedelta(hours = 1),
     token_uri='https://accounts.google.com/o/oauth2/token',
     user_agent='CrOS Info Lookup cros-info.appspot.com')
    try:
      credentials.refresh(httplib2.Http())
    except oauth2client.client.AccessTokenRefreshError:
      self.response.out.write('{"success": false, "error_message": "Please login as an administrator and <a target=\"_blank\" href=\"adminlogin\">authorize this extension."}')
      return
    http = httplib2.Http()
    http = credentials.authorize(http)
    cd = googleapiclient.discovery.build('admin', 'directory_v1', http=http)
    device_info = cd.chromeosdevices().get(customerId='my_customer',
     deviceId=deviceid, projection='FULL', fields=fields).execute()
    device_info['success'] = True
    self.response.out.write(json.dumps(device_info))

class MainHandler(webapp2.RequestHandler):
  def get(self):
    deviceid = self.request.get(argument_name='deviceid', default_value=None)
    fields = self.request.get(argument_name=u'fields', default_value=u'annotatedAssetId,annotatedLocation,annotatedUser,ethernetMacAddress,macAddress,model,notes,orgUnitPath,serialNumber,tpmVersionInfo/firmwareVersion')
    if not deviceid:
      self.response.out.write('<b>Need to specify deviceid</b>')
      return
    primary_domain = self.request.get(argument_name='primary_domain', default_value=None)
    if not primary_domain:
      self.response.out.write('<b>Need to specify primary_domain</b>')
      return
    token = RefreshTokens.get_by_id(id=primary_domain)
    if not token:
      self.response.out.write('Please login as an administrator and <a target="_blank" href="adminlogin">authorize this extension.')
      return
    cs_data = json.loads(open('client_secrets.json').read())
    credentials = oauth2client.client.OAuth2Credentials(
     access_token='',
     client_id=cs_data['web']['client_id'],
     client_secret=cs_data['web']['client_secret'],
     refresh_token=token.refresh_token,
     token_expiry=datetime.datetime.today() - datetime.timedelta(hours = 1),
     token_uri='https://accounts.google.com/o/oauth2/token',
     user_agent='CrOS Info Lookup cros-info.appspot.com')
    try:
      credentials.refresh(httplib2.Http())
    except oauth2client.client.AccessTokenRefreshError:
      self.response.out.write('Please login as an administrator and <a target="_blank" href="adminlogin">authorize this extension.')
      return
    http = httplib2.Http()
    http = credentials.authorize(http)
    cd = googleapiclient.discovery.build('admin', 'directory_v1', http=http)
    device_info = cd.chromeosdevices().get(customerId='my_customer',
     deviceId=deviceid, projection='FULL', fields=fields).execute()
    if u'tpmVersionInfo' in device_info and 'firmwareVersion' in device_info[u'tpmVersionInfo']:
      fwver = device_info[u'tpmVersionInfo'][u'firmwareVersion']
      if fwver in CROS_TPM_VULN_VERSIONS:
        device_info[u'TPM Vulnerability'] = u'<font color="red">Vulnerable</font> - %s' % fwver
      elif fwver in CROS_TPM_FIXED_VERSIONS:
        device_info[u'TPM Vulnerability'] = u'<font color="green">Updated</font> - %s' % fwver
      else:
        device_info[u'TPM Vulnerability'] = u'<font color="green">Not Vulnerable</font> - %s' % fwver
      del(device_info[u'tpmVersionInfo'])
    else:
      device_info[u'TPM Vulnerability'] = u'<font color="orange">Version Not Reported</font>'
    attribute_map = {
          'annotatedLocation': u'Location',
          'macAddress': u'WiFi MAC Address',
          'ethernetMacAddress': u'Ethernet MAC Address',
          'notes': u'Note',
          'serialNumber': u'Serial Number',
          'annotatedUser': u'User',
          'model': u'Model',
          'annotatedAssetId': u'Asset ID',
          'orgUnitPath': u'Organization Unit',
          'bootMode': u'Boot Mode',
          'deviceId': u'Directory API ID',
          'firmwareVersion': u'Firmware Version',
          'lastEnrollmentTime': u'Enrollment Date',
          'lastSync': u'Last policy fetch time',
          'meid': u'MEID',
          'model': u'Model',
          'orderNumber': u'Order Number',
          'osVersion': u'Google Chrome Version',
          'platformVersion': u'Platform Version',
          'recentUsers': u'Recent Users',
          'status': u'Status',
          'supportEndDate': u'Support End Date',
          'willAutoRenew': u'Will Auto Renew'
         }
    self.response.out.write(u'''<!doctype html>
<html>
<header>
<title>Chrome Device Info</title>
</header>
<body>
<style>
      tr:nth-of-type(odd) {
      background-color:#ccc;
    }
</style>
<table width="100%">
 <tbody>
''')
    row_data = {}
    for key, value in device_info.items():
      if key in ['kind', 'etag']:
        continue
      row_key = attribute_map.get(key, key)
      row_value = u''
      if type(value) is list:
        for val in value:
          for k, v in val.items():
            row_value += u'%s: %s<br>' % (k, v)
      elif type(value) in [str, unicode]:
        row_value = value
      row_data[row_key] = row_value
    ordered_keys = [u'Model', u'Serial Number', u'WiFi MAC Address',
        u'Ethernet MAC Address', u'Asset ID', u'User', u'Note',
        u'Location', u'Organization Unit', u'TPM Vulnerability']
    everything_else = filter(lambda a: a not in ordered_keys, row_data.keys())
    row_order = ordered_keys + everything_else
    for ordered_key in row_order:
      if ordered_key in row_data:
        self.response.out.write(u'<tr><td><b>%s</b></td><td>%s</td></tr>\n' % (ordered_key, row_data[ordered_key]))
    self.response.out.write(u'''</tbody
</table>
</body>
</html>''')

class AdminLoginHandler(webapp2.RequestHandler):
  def get(self):
    flow = oauth2client.client.flow_from_clientsecrets(
     'client_secrets.json',
     scope='email https://www.googleapis.com/auth/admin.directory.device.chromeos.readonly https://www.googleapis.com/auth/admin.directory.domain.readonly',
     redirect_uri='https://cros-info.appspot.com/adminlogin')
    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    code = self.request.get(argument_name='code', default_value=None)
    if code:
      try:
        credentials = flow.step2_exchange(code)
      except oauth2client.client.FlowExchangeError:
        self.redirect('/adminlogin')
        return
      http = httplib2.Http()
      http = credentials.authorize(http)
      cd = googleapiclient.discovery.build('admin', 'directory_v1', http=http)
      try:
        domains = cd.domains().list(customer='my_customer').execute()
      except googleapiclient.errors.HttpError, e:
        error = json.loads(e.content)
        http_status = error[u'error'][u'code']
        message = error[u'error'][u'errors'][0][u'message']
        self.response.out.write(u'Oops... It doesn\'t look like you are a super admin. Try logging in as a super admin for a domain which has Chrome devices.<br><br>Error %s: %s' % (http_status, message))
        return
      refresh_token = credentials.refresh_token
      for domain in domains[u'domains']:
        if not domain[u'verified']:
          continue
        token = RefreshTokens(refresh_token=refresh_token)
        token.key = ndb.Key(RefreshTokens, domain[u'domainName'])
        token.put()
      self.response.out.write(u'All finished! Try opening the extenion again now.')
    else:
      auth_uri = str(flow.step1_get_authorize_url())
      self.redirect(auth_uri)

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/adminlogin', AdminLoginHandler),
                               ('/json', JsonHandler)],
                                       debug=False)
