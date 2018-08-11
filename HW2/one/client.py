from socket import *
from select import *
from color import *
from message import *
import sys
import os
import time

class Client:

    def __init__(self, user_id, port, host):
        self.__user_id = user_id
        self.__addr = (host, port)
        self.__socket = None
        self.do_register = False
        self.do_download = False

    def start(self):
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.connect(self.__socket, self.__addr)
        self.__socket.send((MYIDIS + user_id+"#").encode())

    def connect(self, sock, addr):
        try:
            sock.connect(addr)
        except Exception as e:
            print(C_BGRED + "Failed to connect server" + C_END)
            sys.exit()
   
    def show_menu(self):
        print(C_CYAN + "#################################" + C_END)
        print(C_CYAN + "1. Register a file." + C_END)
        print(C_CYAN + "2. Get the global file list." + C_END)
        print(C_CYAN + "3. Download a file." + C_END)
        print(C_CYAN + "4. Exit." + C_END)
        print(C_CYAN + "#################################" + C_END)

    def which_file(self):
        print(C_YELLOW + "which file to register? " + C_END, end = '')
        sys.stdout.flush()
        self.do_register = True

    def which_download(self):
        print(C_YELLOW + "which file to download? " + C_END, end = '')
        sys.stdout.flush()
        self.do_download = True

    def reg_file(self, file_name):
        if os.path.isfile(file_name):
            msg = REGFILE + file_name + "$" + self.__user_id + "#"
            self.__socket.send(msg.encode())
        else:
            print(C_BGRED + "Check your file name again" + C_END)
        self.do_register = False

    def download_file(self, file_name):
        self.__socket.send((REQUEST_FILE + file_name + "/" 
            + self.__user_id + "#").encode())
        self.do_download = False
        return file_name

    def get_file_list(self):
        self.__socket.send((GET_FILE_LIST + self.__user_id + "#").encode())

    def send_file_info(self, msg_content):
        file_name = msg_content.split("$")[0]
        recv_id = msg_content.split("$")[1]
        file_size = 0

        try:
            file_size = os.path.getsize(file_name)
            self.__socket.send((FILE_INFO + str(file_size) 
                + "$" + recv_id + "$" + file_name + "$" 
                + self.__user_id + "#").encode())
        except FileNotFoundError:
            self.__socket.send((FILE_INFO + "-1" + "$" 
                + recv_id + "$" + file_name + "#").encode())
        return file_name, file_size

    def transfer_file(self, file_name, file_size):
        try:
            file_ptr = open(file_name, "rb+")
            cur_size = 0
            while cur_size < file_size:
                if file_size - cur_size > 1024:
                    file_content = file_ptr.read(1024)
                    self.__socket.send(file_content)
                    cur_size += 1024
                else:
                    file_content = file_ptr.read(file_size - cur_size)
                    self.__socket.send(file_content)
                    cur_size = file_size
            file_ptr.close()
            time.sleep(0.1)
        except FileNotFoundError:
            pass

    def get_file_content(self, file_size, file_name):
        write_file = open(file_name, "wb+")
        cur_size = 0
        while cur_size < file_size:
            if file_size - cur_size > 1024:
                file_content = self.__socket.recv(1024)
                write_file.write(file_content)
                cur_size += 1024
            else:
                file_content = self.__socket.recv(file_size - cur_size)
                write_file.write(file_content)
                cur_size = file_size

        write_file.close()
        print(C_GREEN + file_name + " has been downloaded" + C_END)

    def run(self):
        socket_list = [self.__socket, sys.stdin]

        while True:
            try:
                read_list, write_list, except_list = select(socket_list, [], [], 10)
               
                for a_sock in read_list:
                    if a_sock is self.__socket:
                        msg = a_sock.recv(BUF_SIZE).decode()
                        if msg:
                            msg_type = msg.split("#")[0]
                            msg_content = msg.split("#")[1]
            
                            if msg_type == "NOTICE":
                                print(C_BLUE + msg_content + C_END);

                            elif msg_type == "REQUEST_FILE":
                                time.sleep(0.1)
                                file_name, file_size = self.send_file_info(msg_content)
                                time.sleep(0.1)
                                self.transfer_file(file_name, file_size)

                            elif msg_type == "FILE_INFO":
                                file_size = msg_content.split("$")[0]
                                file_name = msg_content.split("$")[1]
                                self.get_file_content(int(file_size), file_name)
                                msg = REGFILE + file_name + "$" + self.__user_id + "#"
                                self.__socket.send(msg.encode())                   
                    else:
                        option = a_sock.readline().rstrip()
                        if option == "0":
                            self.show_menu()
                        elif option == "1":
                            self.which_file()
                        elif option == "2":
                            self.get_file_list()
                        elif option == "3":
                            self.which_download()
                        elif option == "4":
                            self.__socket.close()
                            print(C_YELLOW + "Notified RelayServer" + C_END)
                            print(C_YELLOW + "Goodbye!" + C_END)
                            sys.exit()
                        elif self.do_register:
                            self.reg_file(option)
                        elif self.do_download:
                            self.download_file(option)

                        else:
                            print(C_YELLOW +"Wrong input, type number(0 to 4)" + C_END)
            except KeyboardInterrupt:
                self.__socket.close()
                sys.exit()
                        

if __name__ == "__main__":
    user_id = input(C_BOLD + C_YELLOW + "Enter UserID: " + C_END)
    host_ip = input(C_BOLD + C_YELLOW + "Enter RelayServer Ip address: " + C_END)
    client = Client(user_id, 10080, host_ip)
    client.start()
    client.run()
