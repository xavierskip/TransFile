#!/usr/bin/env python
#coding:utf-8

""" MiniHTTPServer
create the a same other wheel
"""
__version__ = "0.1"


import socket,sys
import os
import time
from  string  import replace
from  urllib2 import unquote # for handle chinse characters

class BaseServer:
	def __init__(self, host, port, pwd):
		self.host = host
		self.port = port
		self.pwd  = pwd
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

	def bind(self):
		self.socket.bind((self.host,self.port))
		self.socket.listen(5)
		print '%s on: http://%s:%d ' %(self.pwd, self.host, self.port)

	def server_forever(self):
		try:
			while True:
				conn,addr = self.socket.accept()
				self.request = conn.recv(2048)
				try:
					response = self.handle_request()
				except Exception, e:
					print 'unknown request!%s\n%s' %(self.request,e)
					continue
				print addr[0],'%s %s' %(self.command, self.src)
				conn.send(response)
				conn.close()
		except KeyboardInterrupt, e:
			self.socket.close()
			self.socket.shutdown(1)
			print '\nserver shut down!'
			exit()

	def handle_request(self):
		self.RequestHeaders = self.parse_request()
		self.command        = self.RequestHeaders['method']
		self.src            = unquote(self.RequestHeaders['requestURL']) # handler chines characters
		do_command     = 'do_'+ self.command
		
		if not hasattr(self,do_command):
			self.send_error(501, "Unsupported method (%r)" % self.command)
			return

		method = getattr(self, do_command)
		response = method() #  do_HEAD() or do_GET() .....
		return response
	#method
	def do_HEAD(self):
		return self.send_response_head()
	
	def do_GET(self):
		self.do_HEAD()
		return self.response_head + self.response_body()
	
	def do_POST():
		pass
	
	def send_error(self, status_code, message):
		self.send_response_line(status_code)
		self.send_header('Content-type','text/html; charset=utf-8')
		self.end_head()
		self.content = message

	def send_response_head(self):
		self.response_head = ''
		self.path = self.translate_path(self.src) # local path
		# directory
		if os.path.isdir(self.path):
			if self.path.endswith('/'):
				self.content = self.directory_page()
				# response head
				self.send_response_line(200)
				self.send_header('Content-type','text/html; charset=utf-8')
				self.send_header('Content-Length',len(self.content))
				self.send_header('Connection','keep-alive')
				self.send_header('server',self.server_version)
				self.send_header('Date',self.GMT_time())
				self.end_head()
				return self.response_head
			else:
				# response head
				self.send_response_line(301)
				self.send_header("Location", self.path + "/")
				self.end_head()
				self.content = '301'
				return self.response_head
		else:
			# File
			self.type = self.guess_type()
			try:
				f = open(self.path,'rb')
				self.content = f.read()
				f.close()
			except IOError:
				self.send_error(404, "<b>%s</b> not found" %self.src)
				return self.response_head
			# response head
			self.send_response_line(200)
			if self.type: 
				self.send_header('Content-type',self.type)
			self.send_header('Content-Length',len(self.content))
			self.send_header('Connection','keep-alive')
			self.send_header('server',self.server_version)
			self.send_header('Date',self.GMT_time())
			#self.send_header('Last_Modified',)
			self.end_head()
			return self.response_head

	# response_head
	def send_response_line(self, status_code):
		self.response_head += '%s %d %s\r\n' %(
			self.protocol_version, 
			status_code,
			self.response_code[status_code][0],)

	def send_header(self, key, value):
		self.response_head += '%s: %s\r\n' %(key,value)

	def end_head(self):
		self.response_head += '\r\n'

	def response_body(self):
		return self.content


	def parse_request(self):
		request_parsed = {}
		request_lines = self.request.rstrip('\r\n').split('\r\n')
		start_line    = request_lines[0].split(' ',2)
		request_parsed['method']     = start_line[0]
		request_parsed['requestURL'] = start_line[1]
		request_parsed['version']    = start_line[2]
		for i in request_lines[1:]:
			header = i.split(':',1)
			request_parsed[header[0]] = header[1]
		return request_parsed	

	def translate_path(self, path):
		# abandon query parameters
		path = path.split('?',1)[0]
		path = path.split('#',1)[0]
		path = replace(path,'..','.')
		path = self.pwd + path
		return path

	def directory_page(self):
		def element(inner,tags):
			return inner.join(tags)
		try:
			list = os.listdir(self.path)
		except os.error:
			self.send_error(404,'No permission to list directory')
		list.sort(key=lambda a: a.lower())
		li = '<li><a href="..">..<a></li>' #back
		for i in list:
			if os.path.isdir(self.path+'/'+i):
				i+='/'
			i = '<a href="%(url)s">%(url)s</a>' %{'url':i}
			li += element(i,['<li>','</li>'])
		ul = element(li,['<ul>','</ul>'])			
		return self.Template %{'title':self.src, 'directory':self.src, 'body':ul}
	
	def guess_type(self):
		Extension = self.path.split('.',-1)[-1]
		try:
			return self.MIME[Extension]
		except KeyError:
			return None
	
	# some other  functions
	def GMT_time(self, timestamp=None):
		if timestamp is None:
			timestamp = time.time()
		year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
		s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % ( 
			 self.weekdayname[wd], 
			 day, self.monthname[month], year,
			 hh, mm, ss)
		return s

	def time_now(self):
		now = time.time()
		year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
		s = "%02d/%3s/%04d %02d:%02d:%02d" % (
			day, self.monthname[month], year, hh, mm, ss)
		return s


	# static class variables
	server_version = "miniHTTP/" + __version__
	protocol_version = 'HTTP/1.1'
	weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
	monthname = [None,
				 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
				 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	MIME = {
		'py': 'text/plain',
		'c': 'text/plain',
		'h': 'text/plain',
		'css': 'text/css',
		'jpg': 'image.jpeg',
		'gif': 'image/gif',
		'swf': 'application/x-shockwave-flash',
		'rar': 'application/octet-stream',
		'tar': 'application/octet-stream',
		'gz':  'application/octet-stream'
	}
	Template = '''
	<!DOCTYPE html>
	<html>
	<head>
		<title>%(title)s</title>
	</head>
	<body style="margin: 0 2em;">
		<p>Directory: <b> %(directory)s</b></p>
		<hr>
		%(body)s
	</body>
	</html>
	'''

	# Table mapping response codes to messages; entries have the
	# form {code: (shortmessage, longmessage)}.
	# See RFC 2616.
	response_code = {
		100: ('Continue', 'Request received, please continue'),
		101: ('Switching Protocols','Switching to new protocol; obey Upgrade header'),
		200: ('OK', 'Request fulfilled, document follows'),
		201: ('Created', 'Document created, URL follows'),
		202: ('Accepted','Request accepted, processing continues off-line'),
		203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
		204: ('No Content', 'Request fulfilled, nothing follows'),
		205: ('Reset Content', 'Clear input form for further input.'),
		206: ('Partial Content', 'Partial content follows.'),

		300: ('Multiple Choices','Object has several resources -- see URI list'),
		301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
		302: ('Found', 'Object moved temporarily -- see URI list'),
		303: ('See Other', 'Object moved -- see Method and URL list'),
		304: ('Not Modified','Document has not changed since given time'),
		305: ('Use Proxy','You must use proxy specified in Location to access this resource.'),
		307: ('Temporary Redirect','Object moved temporarily -- see URI list'),

		400: ('Bad Request','Bad request syntax or unsupported method'),
        401: ('Unauthorized','No permission -- see authorization schemes'),
        402: ('Payment Required','No payment -- see charging schemes'),
		403: ('Forbidden','Request forbidden -- authorization will not help'),
		404: ('Not Found', 'Nothing matches the given URI'),
		405: ('Method Not Allowed','Specified method is invalid for this resource.'),
		406: ('Not Acceptable', 'URI not available in preferred format.'),
		407: ('Proxy Authentication Required', 'You must authenticate with this proxy before proceeding.'),
		408: ('Request Timeout', 'Request timed out; try again later.'),
		409: ('Conflict', 'Request conflict.'),
		410: ('Gone','URI no longer exists and has been permanently removed.'),
		411: ('Length Required', 'Client must specify Content-Length.'),
		412: ('Precondition Failed', 'Precondition in headers is false.'),
		413: ('Request Entity Too Large', 'Entity is too large.'),
		414: ('Request-URI Too Long', 'URI is too long.'),
		415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
		416: ('Requested Range Not Satisfiable','Cannot satisfy request range.'),
		417: ('Expectation Failed','Expect condition could not be satisfied.'),

		500: ('Internal Server Error', 'Server got itself in trouble'),
		501: ('Not Implemented','Server does not support this operation'),
		502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
		503: ('Service Unavailable','The server cannot process the request due to a high load'),
		504: ('Gateway Timeout','The gateway server did not receive a timely response'),
		505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
	}
def test():
	if sys.argv[1:]:
		pwd = sys.argv[1]
	else:
		pwd = os.getcwd()

	httpd = BaseServer('0.0.0.0',8081,pwd)
	httpd.bind()
	httpd.server_forever()

if __name__ == '__main__':
	test()