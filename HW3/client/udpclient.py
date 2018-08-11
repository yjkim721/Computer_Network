from socket import *
import os
import pickle
import random
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

class Packet:

    def __init__(self, seq_num, data):
        self.__seq_num = seq_num
        self.__data = data
        self.__is_send = False
        self.__start_time = -1

    def extract(self):
        return self.__seq_num, self.__data

    def set_start_time(self, start_time):
        self.__start_time = start_time

    def get_start_time(self):
        return self.__start_time

    def set_is_send(self, is_send):
        self.__is_send = is_send

    def get_is_send(self):
        return self.__is_send

class UDPClient:
    BUF_SIZE = 1024 
    def __init__(self, port, ip):
        self.__clientSocket = socket(AF_INET, SOCK_DGRAM)
        self.__port = port
        self.__ip = ip
        self.__addr = (ip, port)
        self.__clientSocket.bind(self.__addr)
    
    def run(self):
        # packet loss 받아오기
        packet_loss = input(C_YELLOW + "packet loss probability: "+C_END)

        # recv buffer 세팅
        recv_buf_size = self.__clientSocket.getsockopt(SOL_SOCKET, SO_SNDBUF)
        print(C_YELLOW + "socket recv buffer size: "+C_END+str(recv_buf_size))
        
        # recv buffer값이 10MB보다 작으면 10MB로 다시 세팅
        if recv_buf_size < 10000000:
            self.__clientSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000000)
            print(C_CYAN+"socket recv buffer size updated: 10000000"+C_END)
            print("")

        while True:
            # 파일 정보 수신
            msg, serverAddress = self.__clientSocket.recvfrom(self.BUF_SIZE)
            file_name = msg.decode().split("/")[0]
            packets_len = int(msg.decode().split("/")[1])

            # 파일 정보 수신함을 알림
            ack = Packet(-2, None)
            self.__clientSocket.sendto(pickle.dumps(ack), serverAddress)

            print(C_CYAN+"The receiver is ready to receive"+C_END)
            print(C_CYAN+"File name is received: "+C_END+file_name)
            print("")

            # write할 파일 열기
            try:
                fp = open(file_name, "wb")
            except IOError:
                return

            expected_num = 0

            # 파일 수신
            start_time = time.time()
            while expected_num < packets_len:
                try:
                    # 패킷 수신
                    pkt, addr = self.__clientSocket.recvfrom(2048)
                    packet = pickle.loads(pkt)
                    seq_num, data = packet.extract()
                    timing = format(time.time() - start_time, '.3f')
                    print(C_PURPLE+timing+" pkt: "+str(seq_num)+" " \
                          +"Receiver < Sender"+C_END)
                    # drop 패킷 여부 확인
                    random_number = random.randint(0, 99)
                    if random_number < int(float(packet_loss) * 100):
                        print(C_GREEN + timing+" pkt: "+str(seq_num)+" " \
                              +"| dropped ")
                    # in order 패킷 이라면
                    elif seq_num == expected_num:
                        ack = Packet(seq_num, None)
                        self.__clientSocket.sendto(pickle.dumps(ack), addr)
                        fp.write(data)
                        timing = format(time.time() - start_time, '.3f')
                        print(C_PURPLE+timing+" ACK: "+str(seq_num)+" " \
                              +"Receiver > Sender"+C_END)
                        expected_num += 1
                    # out order 패킷 이라면
                    else:
                        nak = Packet(expected_num-1, None)
                        self.__clientSocket.sendto(pickle.dumps(nak), addr)
                        timing = format(time.time() - start_time, '.3f')
                        print(C_PURPLE+timing+" ACK: "+str(expected_num-1)+" " \
                              +"Receiver > Sender"+C_END)
                except:
                    pass

            fp.close()
            print(file_name+C_CYAN+" is successfully transferred."+C_END)

if __name__ == "__main__":
    client = UDPClient(10080, "")
    client.run()
