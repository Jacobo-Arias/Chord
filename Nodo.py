import zmq
import json
import string,hashlib,random 
from uuid import getnode as get_mac
from Cliente import Client
import netifaces as ni
from datetime import datetime

# sucesor = context.socket(zmq.PULL)
# clients = context.socket(zmq.REP)

class Node(Client):

    def __init__(self,asdf):
        Client.__init__(self,asdf)
        self.MyId = asdf
        self.MyIp = self.GetIP()
        self.predecessor =  None
        self.successor = self.GetSuccessor()
        self.fingertable = {(str((self.MyId+(i**2))%2**160)) : self.successor for i in range(160)} #!ID:IP
        self.lastUpdate = datetime.now()
        self.updateFingertable()

        self.tonodo = self.context.socket(zmq.PUSH)

        self.fromnodo = self.context.socket(zmq.PULL)
        self.fromnodo.bind("tcp://*5555")

        self.fromclient = self.context.socket(zmq.REP)
        self.fromclient.bind("tcp://*5554")

    def run(self):
	    poller = zmq.Poller()
	    poller.register(self.fromnodo, zmq.POLLIN)
	    poller.register(self.fromclient, zmq.POLLIN)

    def updateFingertable(self):
        self.tonodo.connect(self.successor+'5555')
        self.tonodo.send_json({'newSuccessor':self.fingertable,
                                'idnew':self.MyId,'ipnew':self.MyIp,
                                'time':datetime.now()})
        self.tonodo.disconnect(self.successor+'5555')

    def GetSuccessor(self):
        tempnode = None
        while True:
            comp = self.Coneccion({'pregunta':self.MyId}) #retorna id:ip del iguiente
            if tempnode != comp['nodo']:
                self.IPnode = comp['nodo']
                tempnode = comp['nodo']
            else:
                self.predecessor = self.IPnode
                self.predecessor = self.predecessor.split(':')
                self.predecessor = self.predecessor[0]
                tempnode = self.Coneccion({'newSuccessor':[self.MyId,self.MyIp]})
                return comp['nodo']

    def GetIP(self):
        interfaces = ni.interfaces()
        if 'eth0' in interfaces:
            return ni.ifaddresses('eth0')[2][0]['addr']
        elif 'wlp1s0' in interfaces:
            return ni.ifaddresses('wlp1s0')[2][0]['addr']

    def ObtenerID(self):
        mac = get_mac() #Retorna la direccion mac como entero de 48 bits
        My_id = str(mac).join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                            for x in range(30))
        sha = hashlib.sha1()
        sha.update(My_id.encode('ascii'))
        self.MyId = int(sha.hexdigest() ,16)
        #//bin(_int_)