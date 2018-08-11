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