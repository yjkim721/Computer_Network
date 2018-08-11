from socket import *
from threading import *
from queue import *
import time

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

mutex = Lock()
bottleneck = Queue()
seq_num = 0
ack_num = 0

class Receiver:

    def __init__(self, port, ip):
        self.__link_rate = float(input(C_YELLOW+"Bottle neck link rate: "+C_END))
        self.__queue_size = int(input(C_YELLOW + "Bottle neck queue size: " + C_END))

        self.__client_socket = socket(AF_INET, SOCK_DGRAM)
        self.__port = port
        self.__ip = ip
        self.__addr = (ip, port)
        self.__client_socket.bind(self.__addr)

    def run(self):
        time_stamp_thread = Thread(target=self.timeStamping, args=())
        ack_generate_thread = Thread(target=self.sendAck, args=())

        time_stamp_thread.start()
        ack_generate_thread.start()
        try:
            self.receivePacket()
        except KeyboardInterrupt:
            return

    def receivePacket(self):
        global seq_num, bottleneck
        while True:
            try:
                packet, send_addr = self.__client_socket.recvfrom(1024)
            except ConnectionResetError:
                self.__client_socket.close()
                self.__client_socket = socket(AF_INET, SOCK_DGRAM)
                self.__client_socket.bind(self.__addr)
                continue
            mutex.acquire()
            if bottleneck.qsize() == self.__queue_size:
                self.sendNak(send_addr)
            else:
                bottleneck.put(send_addr)
            seq_num += 1
            mutex.release()

    def sendAck(self):
        global bottleneck, ack_num, mutex

        while True:
            mutex.acquire()
            if bottleneck.qsize() > 0:
                send_addr = bottleneck.get()
                self.__client_socket.sendto("ack".encode(), send_addr)
                ack_num += 1
            mutex.release()
            time.sleep(1.0 / self.__link_rate)

    def timeStamping(self):
        global seq_num, ack_num, bottleneck, f
        time_interval = 0.1
        start_time = time.time()
        while True:
            count = 0
            avg_qsize = 0
            while count < 20:
                avg_qsize += bottleneck.qsize()
                count += 1
                time.sleep(time_interval)
            avg_qsize = (avg_qsize / 20) / self.__queue_size
            current_time = time.time()
            mutex.acquire()
            print("time: {0:0.02f}".format(current_time - start_time))
            print("incoming rate: {0:0.2f}".format(seq_num / 2))
            print("forwarding rate: {0:0.2f} ".format(ack_num / 2))
            print("avg queue occupancy: {0:0.2f} ".format(avg_qsize))
            print("")
            contents = str(current_time - start_time)+","+str(ack_num / 2)+","+str(avg_qsize)+"\n"
            f.write(contents)
            f.flush()
            ack_num = 0
            seq_num = 0
            mutex.release()

    def sendNak(self, send_addr):
        self.__client_socket.sendto("nak".encode(), send_addr)

if __name__ == "__main__":
    with open("./receiver.csv", "w") as f:
        receiver = Receiver(10080, "")
        receiver.run()