#Chord
import zmq
import json
import hashlib

# context = zmq.Context()
# sucesor = context.socket(zmq.PULL)
# clients = context.socket(zmq.REP)

class Client:

    def __init__(self):
        self.node = self.Pedir()
        self.context = zmq.Context()
        self.nodo = self.context.socket(zmq.REQ)
    
    def Pedir(self):
        ipnode = input("Direccion ip conocida: ")
        if not(':' in ipnode):
            ipnode = ipnode + ':5554'
        return ipnode
    
    def Coneccion(self,tosend): #? Mando diccionario, recibo diccionario
        self.nodo.connect('tcp://'+self.node)
        self.nodo.send_json(tosend)
        recvDict = self.nodo.recv_json()
        self.nodo.disconnect('tcp://'+self.node)
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
            if 'other' in recvDict:
                self.node = recvDict['other']
            elif 'parte' in recvDict:
                filename = open('Descargas/'+name,'ab')
                filename.write(recvDict['parte'])
                filename.close()
                if len(hashlist)==0:
                    return 'Listo'
                else:
                    hashid=hashlist.pop()
    
    def Subir(self):
        archivo = input("Nombre del archivo con direcciones: ")
        Guardar = [] #? La lista donde estaran los hash de los pedazos y al final el nombre del archivo
        while True: #?Sacarle hash a cada pedazo y crear el json de las direcciones
            try:
                with open(archivo,"rb") as filef:
                    while True: 
                        contents = filef.read(10*1024*1024)
                        if not contents:
                            break
                        hash_archivo = hashlib.sha256(contents)  
                        sha_file = hash_archivo.hexdigest().encode()
                        Guardar.append(sha_file)
                    filef.close()
                if len(Guardar) == 0:
                    archivo = input("Archivo vacio, ingrese uno valido: ")
                else:
                    Guardar.append(archivo)
                    break
            except:
                archivo = input("Archivo no encontrado, ingrese uno valido: ")
        
        name = input('Con que nombre quiere guardar la llave?: ')
        with open(name, 'w') as outfile:
            json.dump(Guardar, outfile)
            
        Enviar = []
        for Hash01 in Guardar[:-1]:
            recvDict = self.Coneccion({'pregunta':Hash01})
            Enviar.append([Hash01,recvDict['nodo']]) #! HASH,IP
        
        with open(archivo,"rb") as filef:
            # while True:
            for i in range(len(Enviar)): 
                contents = filef.read(10*1024*1024)
                while True: #! Pregunta si la ip que tiene asignada para un hash si corresponde al nodo que lo guarda
                    self.node = Enviar[i][1] #! Si no lo es la reemplaza hasta encontrarla
                    comp = self.Coneccion({'pregunta',Enviar[i][0]})
                    if comp['nodo'] == Enviar[i][1]:
                        break
                    else:
                        Enviar[i][1] = comp['nodo']
                trash = self.Coneccion({'store':[Guardar[i],contents]})
            filef.close()
        print("Archivo subido")
        




# with open(filename,"rb") as filef:
#     hash_archivo = hashlib.sha256()  
#     while True: 
#         contents = filef.read(10*1024*1024)
#         if not contents:
#             break
#         hash_archivo.update(contents) 
#     filef.close() 
            
# sha_file = hash_archivo.hexdigest().encode()

    # def BeNode():
    #     puertos = {
    #         "cliente":"tcp://*:5554",
    #         "predecesor":"tcp://*:5555",
    #         "sucesor":None,
    #         "servers":[]
    #     }
    #     sucesor.bind("tcp://*:5555")
    #     clients.bind("tcp://*:5554")
