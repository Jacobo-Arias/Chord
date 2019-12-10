#Chord
import zmq
import json
import hashlib
import base64

class Client:

    def __init__(self,asdf):
        self.IPnode = asdf
        self.context = zmq.Context()
        self.nodo = self.context.socket(zmq.REQ)
    
    def Pedir(self):
        ipnode = input("Direccion ip conocida: ")
        if not(':' in ipnode):
            ipnode = ipnode + ':5554'
        self.IPnode = ipnode
    
    def Coneccion(self,tosend): #? Mando diccionario, recibo diccionario
        self.nodo.connect('tcp://'+self.IPnode)
        self.nodo.send_json(tosend)
        recvDict = self.nodo.recv_json()
        self.nodo.disconnect('tcp://'+self.IPnode)
        return recvDict

    def Descargar(self):
        archivo = input("Nombre del archivo con direcciones: ")
        while True:
            try:
                with open(archivo) as json_file:
                    hashlist = json.load(json_file)
                name = hashlist.pop(-1)
                break
            except:
                archivo = input("Archivo no encontrado, ingrese uno valido: ")

        hashid = hashlist.pop()
        while True:
            recvDict = self.Coneccion({'hashid':hashid})
            if 'nodo' in recvDict:
                self.IPnode = recvDict['nodo'] + '5554'
            elif 'parte' in recvDict:
                contents = recvDict['parte']
                contents = contents.encode()
                partecita = base64.decodestring(contents)
                filename = open('Descargas/'+name,'ab')
                filename.write(partecita)
                filename.close()
                if len(hashlist)==0:
                    return 'Listo'
                else:
                    hashid=hashlist.pop()
            elif 'Error' in recvDict:
                print('Error 404 not found')
                break
    
    def Subir(self):
        archivo = input("Nombre del archivo: ")
        FileHashes = [] #? La lista donde estaran los hash de los pedazos y al final el nombre del archivo
        while True: #?Sacarle hash a cada pedazo y crear el json de las direcciones
            try:
                with open(archivo,"rb") as filef:
                    while True: 
                        contents = filef.read(10*1024*1024)
                        if not contents:
                            break
                        hash_archivo = hashlib.sha1(contents)  
                        sha_file = hash_archivo.hexdigest()
                        FileHashes.append(sha_file)
                    filef.close()
                if len(FileHashes) == 0:
                    archivo = input("Archivo vacio, ingrese uno valido: ")
                else:
                    FileHashes.append(archivo)
                    break
            except:
                archivo = input("Archivo no encontrado, ingrese uno valido: ")
        
        name = input('Con que nombre quiere guardar la llave?: ')
        with open(name, 'w') as outfile:
            json.dump(FileHashes, outfile)
            
        IPnodes = []
        for Hash01 in FileHashes[:-1]:
            recvDict = self.Coneccion({'pregunta':Hash01})
            IPnodes.append(recvDict['nodo']+':5554') #! IP
        
        with open(archivo,"rb") as filef:
            for i in range(len(IPnodes)): 
                contents = filef.read(10*1024*1024)
                while True: #! Pregunta si la ip que tiene asignada para un hash si corresponde al nodo que lo guarda
                    self.IPnode = IPnodes[i] #! Si no lo es la reemplaza hasta encontrarla
                    comp = self.Coneccion({'pregunta',FileHashes[i]})
                    if comp['nodo'] == IPnodes[i]:
                        break
                    else:
                        IPnodes[i][1] = comp['nodo']
                part = base64.encodestring(contents)
                trash = self.Coneccion({'store':[FileHashes[i],part.decode()]})
            filef.close()
        print("Archivo subido")
        
