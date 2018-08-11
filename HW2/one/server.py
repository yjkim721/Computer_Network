from socket import *
from select import *
from color import *
from message import *
from collections import defaultdict
import sys
import time

class Server:

    def __init__(self, port, host):
        self.__host = host
        self.__port = port
        self.__addr = (self.__host, self.__port)
        self.__socket = None
        self.user_list = {}
        self.file_list = defaultdict(list)

    def start(self):
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.bind(self.__addr)
        self.__socket.listen()

    def run(self):
        socket_list = [self.__socket]

        while True:
            try:
                read_list, write_list, except_list = select(socket_list, [], [], 10)

                for a_sock in read_list:

                    if a_sock is self.__socket:
                        conn_sock, addr = a_sock.accept()
                        socket_list.append(conn_sock)
                        user_id = self.get_usr_id(conn_sock)
                        self.notify_all(self.__socket, WELCOME+user_id+"#", socket_list)

                    else:
                        msg = a_sock.recv(BUF_SIZE).decode()
                        if msg:
                            msg_type = msg.split("#")[0] 
                            msg_content = msg.split("#")[1]
                            if msg_type == "REGFILE":
                                user_id = msg_content.split("$")[1]
                                file_name = msg_content.split("$")[0]
                                self.file_list[user_id].append(file_name)
                                file_list = self.make_file_list()
                                self.notify_all(self.__socket, NOTICE_REGFILE+"#", socket_list)
                            elif msg_type == "GET_FILE_LIST":
                                user_id = msg_content
                                file_list = self.make_file_list()
                                self.user_list[user_id].send((NOTICE + file_list).encode())
                            elif msg_type == "REQUEST_FILE":
                                send_id = msg_content.split("/")[0]
                                send_file = msg_content.split("/")[1]
                                recv_id = msg_content.split("/")[2]
                                self.user_list[send_id].send((REQUEST_FILE 
                                    + send_file + "$" + recv_id + "#").encode())
                                print(C_GREEN+"Received the file download request from "+
                                        recv_id + " for "+ send_id + "/" + send_file + C_END)
                            elif msg_type == "FILE_INFO":
                                file_size = msg_content.split("$")[0]
                                recv_id = msg_content.split("$")[1]
                                file_name = msg_content.split("$")[2]
                                send_id = msg_content.split("$")[3]
                                if int(file_size) > 0:
                                    self.user_list[recv_id].send((FILE_INFO + 
                                        file_size + "$" + file_name + "#").encode())
                                    time.sleep(0.1)
                                    # Get file from sender socket
                                    cur_size = 0
                                    while cur_size < int(file_size):
                                        if int(file_size) - cur_size > 1024:
                                            file_content = a_sock.recv(1024)
                                            cur_size += 1024
                                            self.user_list[recv_id].send(file_content)
                                        else:
                                            file_content = a_sock.recv((int(file_size) - cur_size))
                                            cur_size = int(file_size)
                                            self.user_list[recv_id].send(file_content)
                                    time.sleep(0.1)
                                    print(C_GREEN+"Retrieved " + file_name + 
                                            " from " + send_id + C_END)
                                    print(C_GREEN+"The transfer of "+file_name+" to "
                                            +recv_id+" has been completed"+C_END)
                                else:
                                    self.user_list[recv_id].send(
                                            (NOTICE+"[NOTICE] FILENOTFOUND#").encode())
                        else:
                            socket_list.remove(a_sock)
                            self.notify_all(self.__socket, NOTICE_HAS_LEFT + 
                                    user_id + " has left#", socket_list)
                            user_id = self.get_user_from(a_sock)
                            self.user_list.pop(user_id, None)
                            self.file_list.pop(user_id, None)
                            print(C_GREEN + user_id + " has left" + C_END)
                            self.make_file_list()
                            time.sleep(0.1)
                            self.notify_all(self.__socket, NOTICE_REGFILE+"#", socket_list)
            except KeyboardInterrupt:
                self.__socket.close()
                sys.exit()
                    
    def get_usr_id(self, conn_sock):
        user_id = conn_sock.recv(BUF_SIZE).decode().split("#")[1]
        self.user_list[user_id] = conn_sock
        print(C_GREEN + user_id + " is connected" + C_END)
        return user_id

    def notify_all(self, server, msg, socket_list):
        for a_sock in socket_list:
            if a_sock is not server:
                a_sock.send(msg.encode())

    def make_file_list(self):
        base = "The global file list is as follows:\n"
        base_list = ""
        for user_id, file_list in self.file_list.items():
            for file_name in file_list:
                base_list += user_id + "/" + file_name + "\n"
        print(C_BLUE + base + C_END)
        print(C_CYAN + base_list + C_END)
        return base+base_list

    def get_user_from(self, a_sock):
        for user_id, socket in self.user_list.items():
            if socket == a_sock:
                return user_id
                
if __name__ == "__main__":
    server = Server(10080, "")
    server.start()
    server.run()
