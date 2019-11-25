#Chord
import zmq
import pygame
import string,hashlib,random 
from uuid import getnode as get_mac

context = zmq.Context()
sucesor = context.socket(zmq.PULL)
clients = context.socket(zmq.REP)

class Client():

    def __init__(self):
        self.MyId = self.ObtenerID()
        self.nodes = {}
        self.Pedir()


    def ObtenerID(self):
        mac = get_mac() #Retorna la direccion mac como entero de 48 bits
        My_id = str(mac).join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                            for x in range(30))
        sha = hashlib.sha256()
        sha.update(My_id.encode('ascii'))
        return int(sha.hexdigest() ,16)
        #//bin(_int_)
    
    def Pedir(self):
        ipnode = input("Direccion ip conocida:")
        if not(':' in ipnode):
            ipnode = ipnode + ':5554'
        self.nodes[ipnode] = None

    # def BeNode():
    #     puertos = {
    #         "cliente":"tcp://*:5554",
    #         "predecesor":"tcp://*:5555",
    #         "sucesor":None,
    #         "servers":[]
    #     }
    #     sucesor.bind("tcp://*:5555")
    #     clients.bind("tcp://*:5554")

    fingertable = {('N'+str(i)) : (j+2**i)%300 for i in range(10)}


if __name__ == "__main__":
    nodes = {}
    ipnode = input("Direccion ip conocida:")
    if not(':' in ipnode):
        ipnode = ipnode + ':5554'
    nodes[ipnode] = None
    context = zmq.Context()
    node = context.socket(zmq.REQ)



