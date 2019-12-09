import zmq
import json
import string,hashlib,random 
from uuid import getnode as get_mac
from Cliente import Client
import netifaces as ni
from datetime import datetime
from os import listdir,rmdir
import base64

# sucesor = context.socket(zmq.PULL)
# clients = context.socket(zmq.REP)

class Node(Client):

    def __init__(self,asdf):
        Client.__init__(self,asdf)
        self.MyId = self.ObtenerID()
        self.MyIp = self.GetIP()
        self.predecessorIP =  None
        self.predecessorID =  None
        self.successorID = None
        self.successor = self.GetSuccessor()
        self.fingertable = {((self.MyId+(i**2))%2**160) : self.successor for i in range(160)} #!ID:IP
        self.lastUpdate = datetime.now()
        self.updateFingertable()
        self.tonodo = self.context.socket(zmq.PUSH)

        self.fromnodo = self.context.socket(zmq.PULL)
        self.fromnodo.bind("tcp://*:5555")

        self.fromclient = self.context.socket(zmq.REP)
        self.fromclient.bind("tcp://*:5554")

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
                self.tonodo.connect('tcp://'+self.successor+':5555')
                self.tonodo.send_json(dicSend)
                self.tonodo.disconnect('tcp://'+self.successor+':5555')
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
                    self.tonodo.connect('tcp://'+self.successor+':5555')
                    self.tonodo.send_json(dicSend)
                    self.tonodo.disconnect('tcp://'+self.successor+':5555')
                    
                    bot = self.successorID
                    idaux, ipaux = [0,0]
                    if recv['idnew'] < self.MyId:
                        recv['idnew'] += 2**160
                    for entry in self.fingertable:
                        if bot < (recv['idnew']%2**160) <= entry:
                            idaux = entry
                            ipaux = self.fingertable[entry]
                    for entry in self.fingertable:
                        if self.fingertable[entry] == ipaux and idaux <= entry:
                            self.fingertable[entry] = recv['ipnew']
                else:
                    pass
                recv['idnew']%2**160
                if recv['idnew'] == self.MyId:
                    fingertemp = recv['newnode']
                    for i in self.fingertable:
                        self.fingertable[i] = fingertemp[i]
                    if 'predecesor' in recv:
                        self.predecessorID = recv['predecesor']
            
            elif 'pregunta' in recv:
                intervalo = [self.predecessorID,self.MyId]
                if intervalo[0] < recv['hashid'] <= intervalo[1]:
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
            
            elif 'hashid' in recv:
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
                else: 
                    temp = self.MyId
                    for entry in self.fingertable:
                        if entry < temp:
                            entry += 2**160
                        if recv['hashid'] > temp and recv['hashid'] <= entry:
                            entry %= 2**160
                            self.fromclient.send_json({'ID':entry,'nodo':self.fingertable[entry]})
                        else:
                            entry %= 2**160
                            temp = entry
                    if recv['hashid'] > entry:
                        self.fromclient.send_json({'ID':entry,'nodo':self.fingertable[entry]})
    
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
            
            # elif 'retiro' in recv:
            #     self.tonodo.connect('tcp://'+self.successor+':5555')
            #     self.tonodo.send_json(recv)
            #     self.tonodo.disconnect('tcp://'+self.successor+':5555')
            #     if recv['retiro'] in self.fingertable.values():
            #         valores = self.fingertable.values()
            #         m=[i for i,x in enumerate(valores) if x==recv['retiro']]
            #         reemplazo = list(self.fingertable.keys())[m[-1]+1]
            #         cont = 0
            #         for i in self.fingertable:
            #             if cont in m:
            #                 self.fingertable[i] = reemplazo
            
            # elif 'prpredecessorNew':
            #     self.predecessorID,self.predecessorIP = recv['prpredecessorNew']

            # elif 'successorNew':
            #     self.successorID,self.successor = recv['successorNew']
            
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

    def updateFingertable(self):
        self.tonodo.connect('tcp://'+self.successor+':5555')
        self.tonodo.send_json({'newPredecessor':self.fingertable,
                                'idnew':self.MyId,'ipnew':self.MyIp,
                                'time':datetime.now()})
        self.tonodo.disconnect('tcp://'+self.successor+':5555')

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
                self.predecessorIP = self.predecessor[0]
                tempnode = self.Coneccion({'newSuccessor':[self.MyId,self.MyIp]})
                self.successorID = comp['ID']
                return comp['nodo']

    def GetIP(self):
        interfaces = ni.interfaces()
        if 'eth0' in interfaces: #LAN
            return ni.ifaddresses('eth0')[2][0]['addr']
        elif 'wlp1s0' in interfaces: #WIFI
            return ni.ifaddresses('wlp1s0')[2][0]['addr']

    def ObtenerID(self):
        mac = get_mac() #Retorna la direccion mac como entero de 48 bits
        My_id = str(mac).join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                            for x in range(30))
        sha = hashlib.sha1()
        sha.update(My_id.encode('ascii'))
        self.MyId = int(sha.hexdigest() ,16)
        return  int(sha.hexdigest() ,16)
        #//bin(_int_)
    
    # def retirarse(self):
    #     self.tonodo.connect('tcp://'+self.successor+':5555')
    #     self.tonodo.send_json({'retiro':self.MyIp})
    #     self.tonodo.disconnect('tcp://'+self.successor+':5555')
    #     archivos = listdir('./Files')
    #     for element in archivos:
    #         try:
    #             f = open(element,'r')
    #             file = f.read()
    #             self.tonodo.connect('tcp://'+self.successor+':5555')
    #             self.tonodo.send_json({'toStore':[element,file]})
    #             self.tonodo.disconnect('tcp://'+self.successor+':5555')
    #         except:
    #             pass
    #     rmdir('Files')
    #     self.tonodo.connect('tcp://'+self.successor+':5555')
    #     self.tonodo.send_json({'predecessorNew':[self.predecessorID,self.predecessorIP]})
    #     self.tonodo.disconnect('tcp://'+self.successor+':5555')

    #     self.tonodo.connect('tcp://'+self.predecessorIP+':5555')
    #     self.tonodo.send_json({'successorNew':[self.successorID,self.successor]})
    #     self.tonodo.disconnect('tcp://'+self.predecessorIP+':5555)
