# Simple Web Server

## Introduction
Develop a simple web server using socket programming.

### Server
- Create an HTTP response message consisting of the requested file, and send it to the browser.
- If the browser requests a file that is not present in the web server machine, the web server returns a "404 Not Found" error message.

### Client
- Use existing browsers such as Chrome, Firefox, and Explorer that follow the HTTP standatrd.
- URL format; http://IP_address:portnumber/filename (e.g. http://192.168.0.1:10080/sy.jpg)

## Development Environment
Window10, python 3.6

## Excution
1. Run server.py
2. Send message in browser, such as <code>http://localhost:10080/puppypoop.pdf </code>
3. If the requested file exists, it will show in browser. If not, "404 Not Found" will apear.
