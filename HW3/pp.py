from socket import *
from threading import *
from packet import Packet
import pickle
import math
import os
import time

window = [] # sent packets will be stored in here
win_locker = Lock()
base_time = None


class ReliableSender:

    def __init__(self, port, send_addr, recv_addr, win_size, timeout_val, file_name):
        self.__socket = None
        self.__port = port
        self.__send_addr = send_addr
        self.__recv_addr = recv_addr
        self.__win_size = win_size
        self.__timeout_val = timeout_val
        self.__file_name = file_name

    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_DGRAM)
        self.__socket.bind((self.__send_addr, 0))

    def manage_ack(self, total_packet):
        print("Hello")

    def start(self):
        # initialize global variables
        global base_time
        global win_locker

        # calculate total number of packets and then send file name to receiver
        total_packet = int(math.ceil(os.path.getsize(self.__file_name) / 1024))
        f = open(self.__file_name, "rb")
        self.__socket.sendto(self.__file_name.encode(), self.__recv_addr)

        # create ACK receiving thread and initialize starting time
        ack_manager = Thread(target=self.manage_ack, args=(total_packet, ))
        ack_manager.start()
        base_time = time.time()



if __name__ == "__main__":
    recv_addr = (input("Receiver IP address: "), 10080)
    win_size = int(input("window size: "))
    timeout_val = float(input("timeout (sec): "))
    file_name = input("file name: ")
    print("")
    sender = ReliableSender(0, "", recv_addr, win_size, timeout_val, file_name)
    sender.init_socket()
    sender.start()