from socket import *
import os
import mimetypes

# parsing request, return request file_name(path) and file_type(type)
def get_path(msg):
    # split message with ' '
    total_msgs1 = msg.split(' ')
    path = total_msgs1[1]                   # 1th element should be file_name (e.g. /abc.jpg)
    path = path[1:]                         # remove '/' (e.g. abc.jpg)

    # split file_name(path) with '.'
    total_msgs2 = path.split('.')
    last = len(total_msgs2)
    type = total_msgs2[last-1]              # last element of path is file_type
    return path, type

# making http header
def make_http_header(exist, extension, file_size):

    # set str_status
    if exist:                               # if file exists
        str_status = "200 OK"
        str_type = mimetypes.types_map.get("."+extension, "application/octet-stream")
    else:                                   # if file does not exist
        str_status = "404 Not Found"
        str_type = "text/plain"

    # generate http_header using str_status, str_type, and file_size
    http_header = "HTTP/1.0 "+str_status+"\r\nContent-type: "+str_type+"\r\nContent-Length: "+str(file_size)+"\r\n\r\n"

    return http_header

# set serverSocket
serverPort = 10080
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(10)
print('The TCP server is ready to receive.')

# loop for connecting socket
while True:
    connectionSocket, addr = serverSocket.accept()
    print("Server is connected with client")
    msg = connectionSocket.recv(1024).decode()

    if msg is not "":   # error handling for empty message
        request, type = get_path(msg)
        exist = os.path.isfile(request)

        if exist:   # if file exists,
            file = open(request, 'rb')
            file_size = os.path.getsize(request)
            buf = file.read(file_size)
        else:       # if file does not exist
            file_size = 13  # size for error message "404 Not Found"
            type = "not_exist"
            print("requested file do not exists")

        # make http_header
        http_header = make_http_header(exist, type, file_size)
        # send http_header
        connectionSocket.send(http_header.encode())
        # send contents
        if exist:
            connectionSocket.send(buf)
        else:
            connectionSocket.send("404 Not Found".encode())
    connectionSocket.close()
