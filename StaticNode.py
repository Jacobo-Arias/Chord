import zmq
import json
import string,hashlib,random 
from uuid import getnode as get_mac
from Cliente import Client
import netifaces as ni
from datetime import datetime
from os import listdir
import base64

# sucesor = context.socket(zmq.PULL)
# clients = context.socket(zmq.REP)

class Node():

    def __init__(self):
        self.MyId = self.ObtenerID()
        self.MyIp = self.GetIP()
        self.predecessorIP =  None
        self.predecessorID =  None
        self.successorID = None
        self.successor = None
        self.fingertable = {((self.MyId+(i**2))%2**160) : self.MyIp for i in range(160)} #!ID:IP
        self.lastUpdate = datetime.now()
        
        self.context = zmq.Context()
        self.tonodo = self.context.socket(zmq.PUSH)

        self.fromnodo = self.context.socket(zmq.PULL)
        self.fromnodo.bind("tcp://*:5555")

        self.fromclient = self.context.socket(zmq.REP)
        self.fromclient.bind("tcp://*:5554")
        self.start()

    def start(self):
        self.successor = input("Ip next: ")
        self.tonodo.connect('tcp://'+ self.successor +':5555')
        self.tonodo.send_json(self.MyId)
        self.tonodo.disconnect('tcp://'+ self.successor +':5555')
        self.successorID = self.fromnodo.recv_json()
        for  oneID in self.fingertable:
            if self.successorID > self.MyId:
                if self.MyId < oneID <= self.successorID:
                    self.fingertable[oneID] = self.successor
            elif self.successorID < self.MyId:
                if oneID > self.MyId or oneID <= self.successorID:
                    self.fingertable[oneID] = self.successor
                


    def run(self):
        poller = zmq.Poller()
        poller.register(self.fromnodo, zmq.POLLIN)
        poller.register(self.fromclient, zmq.POLLIN)

        recvlist = []
        while True:
            socks = dict(poller.poll()) 
            if self.fromnodo in socks:
                recvlist.append(self.fromnodo.recv_json())
            if self.fromclient in socks:
                recvlist.append(self.fromclient.recv_json())
                self.fromclient.send_json([])
            
            recv = recvlist.pop()
            if 'newSuccessor' in recv:
                successor = recv['newSuccessor'] #ID,IP
                # if self.predecessorID < self.successorID:
                for F_id in self.fingertable:
                    if successor[0] <= F_id:
                        self.fingertable[F_id] = successor[1]
                # elif:
                #     for F_id in self.fingertable:
                #         if successor[0] <= F_id:
                #             self.fingertable[F_id] = successor[1]
                
                self.successor = successor[1]
                self.successorID = successor[0]
                self.fromclient.send_json({'nodo':self.MyIp,'ID':self.MyId})

            if 'newPredecessor' in recv:
                self.predecessorID = recv['idnew']
                self.predecessorIP = recv['ipnew']
                dicSend = {'idnew':recv['idnew'],'ipnew':recv['ipnew'],'time':recv['time']}
                fingertemp = recv['newSuccesor']
                if recv['idnew'] in self.fingertable:
                    self.fingertable[recv['idnew']] = recv['ipnew']
                for fingerT in fingertemp:
                    if fingerT in self.fingertable:
                        fingertemp[fingerT] = self.fingertable[fingerT]
                dicSend['newnode']=fingertemp
                self.tonodo.connect(self.successor)
                self.tonodo.send_json(dicSend)
                self.tonodo.disconnect(self.successor)
                self.send_files()


            elif 'newnode' in recv:
                if self.lastUpdate < recv['time']:
                    dicSend = {'idnew':recv['idnew'],'ipnew':recv['ipnew'],'time':recv['time']}
                    self.lastUpdate = recv['time']
                    if recv['ipnew'] == self.successor:
                        dicSend['predecesor'] = self.MyId
                    fingertemp = recv['newnode']
                    for entry in fingertemp:
                        if entry in self.fingertable:
                            fingertemp[entry] = self.fingertable[entry]
                    dicSend['newnode']=fingertemp
                    self.tonodo.connect(self.successor)
                    self.tonodo.send_json(dicSend)
                    self.tonodo.disconnect(self.successor)
                else:
                    pass
                if recv['idnew'] == self.MyId:
                    fingertemp = recv['newnode']
                    for i in self.fingertable:
                        self.fingertable[i] = fingertemp[i]
            
            elif 'pregunta' in recv:
                intervalo = [self.predecessorID,self.MyId]
                if recv['pregunta'] == self.MyId:
                    self.fromclient.send_json({'nodo':self.MyIp,'ID':self.MyId})
                else:
                    temp = self.MyId
                    for entry in self.fingertable:
                        if entry < temp:
                            entry += 2**160
                        if recv['pregunta'] > temp and recv['pregunta'] <= entry:
                            entry %= 2**160
                            self.fromclient.send_json({'ID':entry,'nodo':self.fingertable[entry]})
                        else:
                            entry %= 2**160 
                            temp = entry
                    if recv['pregunta'] > entry:
                        self.fromclient.send_json({'ID':entry,'nodo':self.fingertable[entry]})
            
            elif 'hasid' in recv:
                intervalo = [self.predecessorID,self.MyId]
                if intervalo[0] < recv['hashid'] <= intervalo[1]:
                    try:
                        mensaje = open('./Files' + recv['hashid'],'rb')
                        contents = mensaje.read()
                        mensaje.close()
                        part = base64.encodestring(contents)
                        self.fromclient.send_json({'parte':part.decode()})
                    except:
                        self.fromclient.send_json({'Error':404})
    
            elif 'store' in recv:
                name,part = recv['store']
                part = part.encode()
                partecita = base64.decodestring(part)
                f = open('./Files'+name,'ab')
                f.write(partecita)
                f.close()
                self.fromclient.send_json({'Hola':'Mundo'})
            
            elif 'toStore' in recv:
                name,part = recv['toStore']
                f = open('./Files'+name,'ab')
                f.write(part)
                f.close()
            
    def send_files(self):
        archivos = listdir('./Files')
        for element in archivos:
            try:
                hasid = int(element)
                if hasid <= self.predecessorID:
                    f = open(element,'r')
                    file = f.read()
                    self.tonodo.connect('tcp://'+self.predecessorIP+':5555')
                    self.tonodo.send_json({'toStore':[element,file]})
                    self.tonodo.disconnect('tcp://'+self.predecessorIP+':5555')
            except:
                pass

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
        return  int(sha.hexdigest() ,16)

if __name__ == "__main__":
    Myself = Node()
    print('Ejecutando como Nodo con:\n IP: '+ Myself.MyIp + '\n ID: ' + Myself.MyId)
    Myself.run()