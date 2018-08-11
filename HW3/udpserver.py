from socket import *
from threading import *
import os
import pickle
import time

base = 0
mutex = Lock()
duplicated_ack_num = 0
next_to_send = 0
start_time = time.time()
connected = False

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

class UDPServer:
    
    BUF_SIZE = 1024

    def __init__(self, port, host_addr):
        # window size, time out, file name을 받아온다
        self.__recvIp = input(C_YELLOW+"Receiver Ip address: "+C_END)
        self.__window_size = input(C_YELLOW+"window size: "+C_END)
        self.__timeout = input(C_YELLOW+"timeout (sec): "+C_END)
        self.__file_name = input(C_YELLOW+"file name: "+C_END)

        self.__serverSocket = socket(AF_INET, SOCK_DGRAM)
        self.__port = port
        self.__host_addr = host_addr
        self.__serverSocket.bind((host_addr, port))
        self.__start_time = -1

    def run(self):
        # 연결된 receiver한테 파일을 전송한다
        clientAddress = (self.__recvIp, 10080)
        self.sendFile(clientAddress)

    def sendFile(self, addr):
        global mutex
        global base
        global next_to_send
        global duplicated_ack_num
        global start_time
        global connected

        # 파일 열기, 파일 크기 알아내기
        try:
            fp = open(self.__file_name, "rb+")
            file_size = os.path.getsize(self.__file_name)            
        except FileNotFoundError:
            pass

        # 패킷 리스트 세팅
        packets = []
        seq_num = 0

        # 패킷 리스트 만들기
        while True:
            # 버퍼의 크기만큼 파일 읽기
            data = fp.read(self.BUF_SIZE)
            if not data:
                break
            # 패킷으로 만들기
            packet = Packet(seq_num, data)
            # 패킷리스트에 추가
            packets.append(packet)
            # sequence number 증가
            seq_num += 1

        # 파일 송신 전 세팅
        num_packets = len(packets)
        base = 0
        next_to_send = 0
        duplicated_ack_num = 0

        # ack 수신 쓰레드 생성
        t = Thread(target=self.receiveAck, args=(addr,num_packets ))
        t.start()

        # receiver 찾기
        c = 0
        while not connected:
            # 파일 정보 보내기
            message = self.__file_name + "/" + str(num_packets)
            self.__serverSocket.sendto(message.encode(), addr)
            if c % 100 == 0:
                print("...finding receiver...")
            c += 1

        # 모든 패킷을 전송할 때까지 반복
        self.__start_time = time.time()
        start_time = self.__start_time

        while base < num_packets:

            # 윈도우 안에 있는 모든 패킷을 전송
            window_size = int(self.__window_size)
            while next_to_send < base + window_size:
                if next_to_send < num_packets:
                    # 해당 패킷을 보낸 적이 있는 지 판단, 보낸 적이 없는 패킷만 전송
                    if packets[next_to_send].get_is_send() is False:
                        # 패킷 전송
                        self.sendPacket(time.time(),next_to_send,packets,addr,"")
                        next_to_send += 1
                # 패킷 모두 보냄
                else:
                    break

            if base < num_packets and packets[base].get_is_send():
                try:
                    # base 패킷의 ACK를 받았거나, timeout이 되거나, 3 duplicated ACKs을 받을 때까지
                    mutex.acquire()
                    timeout_value = time.time()-packets[base].get_start_time()
                    while timeout_value < float(self.__timeout) and (duplicated_ack_num < 3):
                        mutex.release()
                        time.sleep(0.05)
                        mutex.acquire()
                        timeout_value = time.time()-packets[base].get_start_time()
                    mutex.release()

                    # 3 duplicated ACKs을 받은 경우
                    if packets[base].get_is_send() and duplicated_ack_num>=3:
                        timing = format(time.time() - start_time, '.3f')
                        print(C_GREEN+timing+" pkt: "+str(base-1)+" " \
                                + "| 3 duplicated ACKs"+C_END)
                        # 3 duplicated ack에 해당하는 패킷 보내기
                        self.sendPacket(time.time(), base, packets, addr, "(retransmission)")
                    # timeout이 된 경우
                    elif packets[base].get_is_send() and timeout_value >= float(self.__timeout):
                        timing = format(time.time() - start_time, '.3f')
                        tv = format((time.time()-packets[base].get_start_time()), '.3f')
                        print(C_GREEN+timing+" pkt: "+str(base)+" " \
                                    + "| timeout since "+str(tv)+C_END)
                        # timeout ack에 해당하는 패킷 보내기
                        self.sendPacket(time.time(), base, packets, addr, "(retransmission)")
                    # Ack를 받은 경우
                    else:
                        pass
                except:
                    pass

        end_time = time.time()

        # 파일 닫기
        fp.close()

        # 종료
        throughput = num_packets / (end_time - start_time)
        throughput_str = format(throughput, '.2f')
        print(self.__file_name+C_YELLOW+" is successfully transferred."+C_END)
        print(C_YELLOW+"Throughput: "+C_END+ throughput_str + "pkts / sec")

    def sendPacket(self, cur_time, packet_num, packets, recv_addr, msg1):
        # 패킷 전송
        timing = format(cur_time - self.__start_time, '.3f')
        print(C_PURPLE + timing + " pkt: " + str(packet_num) + " " \
              + "Sender > Receiver" + C_END + C_CYAN + msg1 + C_END)
        packet_to_send = pickle.dumps(packets[packet_num])
        self.__serverSocket.sendto(packet_to_send, recv_addr)
        # 패킷을 보냈는지, 패킷을 보낸 시간을 기록해둠
        packets[packet_num].set_is_send(True)
        packets[packet_num].set_start_time(time.time())

    def receiveAck(self, addr, num_packets):
        global mutex
        global base
        global duplicated_ack_num
        global start_time
        global connected

        count = 0
        while count < num_packets:
            data, clientAddress = self.__serverSocket.recvfrom(1024)
            packet = pickle.loads(data)
            ack, _ = packet.extract()

            # receiver 찾음
            if ack == -2:
                connected = True
            else:
                timing = format(time.time() - start_time, '.3f')
                print(C_PURPLE+timing+" ACK: "+str(ack)+" " \
                        + "Sender < Receiver"+C_END)

                # 제대로 된 ack를 받았다면
                if ack >= base:
                    mutex.acquire()
                    base = ack + 1
                    count += 1
                    duplicated_ack_num = 0
                    mutex.release()
                # out order ack를 받았다면
                else:
                    mutex.acquire()
                    duplicated_ack_num += 1
                    mutex.release()

if __name__ == "__main__":
    server = UDPServer(0, "")
    server.run()
