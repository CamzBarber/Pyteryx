import time
import json
import sys
import requests
from requests_ntlm import HttpNtlmAuth
from pandas import read_csv
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


class Pyteryx(object):
	
	def __init__(self, host, user, pwrd):
		self.hostname = host
		self.username = user
		self.password = pwrd
		self.session_id = self.__get_session_id(self.hostname, self.username, self.password)
		self.headers = {
			'X-Authorization': self.session_id,
			'Content-Type': 'application/json',
    	}


	def __get_session_id(self, host, user, pwrd):
		headers = {
			'Content-Type': 'application/json',
		}

		data = {'scheme': 'windows', 'parameters': [{'name': 'updateLastLoginDate', 'value': True}]}

		response = requests.post(host + '/gallery/api/auth/sessions/',
								 auth=HttpNtlmAuth(user, pwrd),
								 headers=headers,
								 data=json.dumps(data))

		session_id = 'SPECIAL ' + response.json()['sessionId']
		return session_id


	def get_all_private_workflows(self, search=None, limit=None, offset=None, package_type=None):
		params = (
			('search', search),
			('limit', limit),
			('offset', offset),
			('packageType', package_type),
			('_', str(int(round(time.time() * 1000)))),
		)
		
		response = requests.get(self.hostname + '/gallery/api/apps/studio/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)
		
		private_workflows = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return private_workflows

	
	def get_all_collection_workflows(self, appLimit=None):
		params = (
			('appLimit', '5'),
			('_', str(int(round(time.time() * 1000)))),
		)
		
		response = requests.get(self.hostname + '/gallery/api/collections/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)

		collection_workflows = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return collection_workflows
	
	
	def get_workflow_info(self, app_id):
		response = requests.get(self.hostname + '/gallery/api/apps/' + app_id + '/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers)
		
		workflow_info = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return workflow_info

	
	def get_workflow_questions(self, app_id):
		params = (
			('useDefaultCredentials', 'true'),
			('_', str(int(round(time.time() * 1000)))),
		)
		
		response = requests.get(self.hostname + '/gallery/api/apps/' + app_id + '/interface',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)

		workflow_questions = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return workflow_questions
		
		
	def run_workflow(self, app_id, questions=None):
		data = {
			'appPackage': {
				'id': app_id
			},
			'jobName': '',
			'useDefaultCredentials': True,
			'version': '',
			'questions': questions
		}
		
		response = requests.post(self.hostname + '/gallery/api/apps/jobs/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								data=json.dumps(data))
		
		workflow_info = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return workflow_info

	
	def get_workflow_status(self, instance_id):
		params = (
        	('_', str(int(round(time.time() * 1000)))),
		)
		
		response = requests.get(self.hostname + '/gallery/api/apps/jobs/' + instance_id + '/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)
		
		workflow_status = {
			'status': response.status_code,
			'results': response.json()
		}
		
		return workflow_status


	def __get_workflow_output(self, instance_id):
		params = (
			('_', str(int(round(time.time() * 1000)))),
		)

		response = requests.get(self.hostname + '/gallery/api/apps/jobs/' + instance_id + '/output/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)

		workflow_output = {
			'status': response.status_code,
			'results': [x['id'] for x in response.json()]
		}

		return workflow_output


	def __get_workflow_output_token(self):
		params = (
			('_', str(int(round(time.time() * 1000)))),
		)

		response = requests.get(self.hostname + '/gallery/api/auth/token/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)

		workflow_token = {
			'status': response.status_code,
			'results': response.json()['token']
		}

		return workflow_token


	def __get_workflow_data(self, token, instance_id, output_id):
		params = (
			('format', 'raw'),
			('web_token', token),
		)

		response = requests.get(self.hostname + '/gallery/api/apps/jobs/' + instance_id + '/output/' + output_id + '/',
								auth=HttpNtlmAuth(self.username, self.password),
								headers=self.headers,
								params=params)

		workflow_data = {
			'status': response.status_code,
			'results': response.text
		}

		return workflow_data


	def get_workflow_result(self, instance_id):
		output_ids = self.__get_workflow_output(instance_id)
		workflow_data = []
		if len(output_ids['results']) >= 1:
			output_token = self.__get_workflow_output_token()
			for i in output_ids['results']:
				workflow_content = self.__get_workflow_data(output_token['results'], instance_id, i)
				workflow_data.append(read_csv(StringIO(workflow_content['results'])))

		workflow_output = {
			'status': workflow_content['status'],
			'results': workflow_data
		}

		return workflow_output


	def run_workflow_get_result(self, app_id, questions=None):
		instance_id = self.run_workflow(app_id, questions)['results']['id']
		status_flag = None
		while status_flag != 'Completed':
			status = self.get_workflow_status(instance_id)['results']
			status_flag = status['status']
			print(status['status'], status['disposition'])
			time.sleep(1)

		return self.get_workflow_result(instance_id)
