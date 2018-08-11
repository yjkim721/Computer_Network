from socket import *
from threading import *
from random import *
import time
import math
import sys

C_END     = "\033[0m"
C_BOLD    = C_END + "\033[1m"
C_INVERSE = C_END + "\033[7m"

C_BLACK  = C_END + "\033[30m"
C_RED    = C_END + "\033[31m"
C_GREEN  = C_END + "\033[32m"
C_YELLOW = C_END + "\033[33m"
C_BLUE   = C_END + "\033[34m"
C_PURPLE = C_END + "\033[35m"
C_CYAN   = C_END + "\033[36m"
C_WHITE  = C_END + "\033[37m"

C_BGBLACK  = C_END + "\033[40m"
C_BGRED    = C_END + "\033[41m"
C_BGGREEN  = C_END + "\033[42m"
C_BGYELLOW = C_END + "\033[43m"
C_BGBLUE   = C_END + "\033[44m"
C_BGPURPLE = C_END + "\033[45m"
C_BGCYAN   = C_END + "\033[46m"
C_BGWHITE  = C_END + "\033[47m"

seq_num = 0
ack_num = 0
sending_rate = 0
mutex = Lock()
f = None

class Sender:
    def __init__(self, port, addr):
        global sending_rate
        self.__recvIp = input(C_YELLOW+"Receiver Ip address: "+C_END)
        self.__sending_rate = input(C_YELLOW+"Initial Sending rate(pps): "+C_END);
        self.__sender_socket = socket(AF_INET, SOCK_DGRAM)
        self.__port = port
        self.__host_addr = addr
        self.__sender_socket.bind((addr, port))
        self.__reciever_addr = (self.__recvIp, 10080)
        sending_rate = float(self.__sending_rate)

    def run(self):
        global seq_num, sending_rate
        time_stamp_thread = Thread(target=self.timeStamping, args=())
        receive_ack_thread = Thread(target=self.receiveAck, args=())
        time_stamp_thread.start()
        receive_ack_thread.start()
        try:
            self.sendPacket()
        except KeyboardInterrupt:
            return

    def sendPacket(self):
        global seq_num
        while True:
            packet = str(seq_num)
            while sys.getsizeof(packet) < 1000:
                packet += "\0"
            self.__sender_socket.sendto(packet.encode(), self.__reciever_addr)
            seq_num += 1

            time.sleep(1.0 / sending_rate)

    def receiveAck(self):
        global ack_num, sending_rate
        while True:
            msg, client_addr = self.__sender_socket.recvfrom(1024)
            ack = msg.decode()
            mutex.acquire()
            if ack == "nak":
                sending_rate = ( sending_rate - 3 / sending_rate ) * 1 / 2
            elif ack == "ack":
                ack_num += 1
                sending_rate = sending_rate + 1 / sending_rate * 1 / 2
            mutex.release()

    def timeStamping(self):
        global seq_num, ack_num, f

        time_interval = 2
        start_time = time.time()
        while True:
            current_time = time.time()
            mutex.acquire()
            if seq_num != 0:
                goodput_ratio = ack_num / seq_num
            else:
                goodput_ratio = 0

            print("time: {0:0.2f}".format(current_time - start_time))
            print("sending rate: {0:0.2f} pps".format(seq_num / 2))
            print("goodput: {0:0.2f} pps".format(ack_num / 2))
            print("goodput ratio: {0:0.02f}".format(goodput_ratio))
            print("")
            contents = str(current_time - start_time)+","+str(ack_num / 2)+","+str(goodput_ratio)+"\n"
            f.write(contents)
            f.flush()
            ack_num = 0
            seq_num = 0
            mutex.release()
            time.sleep(time_interval)

if __name__ == "__main__":
    port = randint(11000, 12000)
    print(C_BOLD+"port : "+str(port)+C_END)
    with open("./sender_port_"+str(port)+".csv", "w") as f:
        sender = Sender(port, "")
        sender.run()