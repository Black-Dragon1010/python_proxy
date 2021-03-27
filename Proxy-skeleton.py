# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re
from urllib2 import urlopen

##### user function definition start #####
# fetch from cache function
def fetchFromCache(filename):
  try:
    # check if it is in local cache directory
    cache_file = open(filename, 'r')
    content = cache_file.readlines()
    cache_file.close()
    print content
    # if success, returns it.
    return content
  except IOError:
    return None

# save in local cache function
def saveInCache(filename, file_content):
  print('Saving a new file in the cache directory')
  cache_file = open(filename, 'w')
  cache_file.write(file_content)
  cache_file.close()
##### user function definition end #####

# 1MB buffer size
#Define constant variables
BUFFER_SIZE = 1000000
SOCKET_CONS = 50

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()


# Create a server socket, bind it to a port and start listening
# The server IP is in args.hostname and the port is in args.port
# bind() accepts an integer only
# You can use int(string) to convert a string to an integer

try:
  # Create a server socket
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  print 'Connected socket'
except:
  print 'Failed to create socket'
  sys.exit()

try:
  # Bind the the server socket to a host and port
  serverSocket.bind((args.hostname, int(args.port)))
  print 'Port is bound'
except:
  print('Port is in use')
  sys.exit()
serverSocket.listen(SOCKET_CONS)
try:
  # Listen on the server socket
  serverSocket.listen(SOCKET_CONS)
  print 'Listening to socket'
except:
  print 'Failed to listen'
  sys.exit()

while True:
  print 'Waiting connection...'

  clientConnect = None
  try:
    # Accept connection from client and store in the clientSocket
    print 'Accept connection from client...'
    clientConnect, client_addr = serverSocket.accept()
    
    print 'Received a connection from:', args.hostname
  except:
    print 'Failed to accept connection'
    sys.exit()

  message = 'METHOD URI VERSION'
  # Get request from client
  # and store it in message
  # thread.start_new_thread(proxy_thread, (clientConnect, client_addr))
  message = clientConnect.recv(BUFFER_SIZE)

  print 'Received request:'
  print '< ' + message

  # Extract the parts of the HTTP request line from the given message
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print 'Method:\t\t' + method
  print 'URI:\t\t' + URI
  print 'Version:\t' + version
  print ''

  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, 1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')
  print 'Neat URI:' + URI
  # Split hostname from resource
  resource_part = URI.split('/', 1)
  hostname = resource_part[0]
  resource = '/'

  if len(resource_part) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resource_part[1]

  print 'Requested Resource:\t' + resource

  cacheLocation = './cache/' + hostname + resource
  if cacheLocation.endswith('/'):
    cacheLocation = cacheLocation + 'default'

  print 'Cache location:\t\t' + cacheLocation

  fileExists = os.path.isfile(cacheLocation)

  try:
    # Check whether the file exist in the cache
    cacheFile = open(cacheLocation, "r")
    outputdata = cacheFile.readlines()

    print 'Cache hit! Loading from cache file: ' + cacheLocation
    # ProxyServer finds a cache hit
    # Send back contents of cached file
    clientConnect.send("HTTP/1.0 200 OK\r\n")
    clientConnect.send("Content-Type:text/html\r\n")
    for i in range(0, len(outputdata)):
      clientConnect.send(outputdata[i])
    print 'Read from Cache'

    cacheFile.close()

  # Error handling for file not found in cache
  except IOError:
    if fileExists:
      clientResponse = ''
      # If we get here, the file exists but the proxy can't open or read it
      # What would be the appropriate status code and message to send to client?
      # store the value in clientResponse
      # store the vlaue in the cache location and send the value to the client
      clientResponse = fetchFromCache(cacheLocation)
      cacheFile = open(cacheLocation, "r")
      outputdata = cacheFile.readlines()
      print 'Sending to the client:'
      clientConnect.send("HTTP/1.0 200 OK\r\n")
      clientConnect.send("Content-Type:text/html\r\n")
      for i in range(0, len(outputdata)):
        clientConnect.send(outputdata[i])

    else:
      originServerSocket = None
      # Create a socket to connect to origin server
      # and store in originServerSocket
      print 'Creating a socket on proxy server:'
      originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

      hostname = hostname.replace("www.", "", 1)
      print 'Connecting to:\t\t' + hostname + '\n'
      try:
        # Get the IP address for a hostname
        address = socket.gethostbyname(hostname)

        # Connect to the origin server
        originServerSocket.connect((hostname, 80))

        print 'Connected to origin Server', address

        # Create a file object associated with this socket
        # This lets us use file function calls
        originServerFileObj = originServerSocket.makefile('r', 0)

        originServerRequest = ''
        originServerRequestHeader = ''
        # Create origin server request line and headers to send
        # and store in originServerRequestHeader and originServerRequest
        # originServerRequest is the first line in the request and
        # originServerRequestHeader is the second line in the request
        originServerRequest = 'GET / HTTP/1.1'
        originServerRequestHeader = 'Host: ' + hostname

        # Construct the request to send to the origin server
        request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

        # Request the web resource from origin server
        print 'Forwarding request to origin server:'
        for line in request.split('\r\n'):
          print '> ' + line

        try:
          originServerSocket.sendall(request)
        except socket.error:
          print 'Send failed'
          sys.exit()

        originServerFileObj.write(request)

        # Get the response from the origin server
        response = originServerSocket.recv(BUFFER_SIZE)
        # print response

        # Send the response to the client
        clientConnect.sendall(response)

        # finished sending to origin server - shutdown socket writes
        originServerSocket.shutdown(socket.SHUT_WR)

        print 'Request sent to origin server\n'

        # Create a new file in the cache for the requested file.
        # Also send the response in the buffer to client socket
        # and the corresponding file in the cache
        cacheDir, file = os.path.split(cacheLocation)
        print 'cached directory ' + cacheDir
        if not os.path.exists(cacheDir):
          os.makedirs(cacheDir)
        cacheFile = open(cacheLocation, 'wb')

        # Save orogin server response in the cache file
        saveInCache(cacheLocation ,response)

        print 'done sending'
        originServerSocket.close()
        cacheFile.close()
        print 'cache file closed'
        clientConnect.shutdown(socket.SHUT_WR)
        print 'client socket shutdown for writing'
      except IOError, (value, message):
        print 'origin server request failed. ' + message
  try:
    clientConnect.close()
  except:
    print 'Failed to close client socket'


