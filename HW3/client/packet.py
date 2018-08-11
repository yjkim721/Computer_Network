class Packet:

    def __init__(self, seq_num, data):
        self.__seq_num = seq_num
        self.__data = data
    
    def extract(self):
        return self.__seq_num, self.__data
