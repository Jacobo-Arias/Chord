import Nodo
import Cliente


Myself = Cliente.Client('a')
Myself.Pedir()

while True:
    op = int(input(' 1. Descargar \n 2. Subir \n 3. Ser servidor \n 0.Salir'))
    if op == 0:
        print('Bye')
        break
    elif op == 1:
        Myself.Descargar()
    elif op == 2:
        Myself.Subir()
    elif op == 3:
        Myself = Nodo.Node(Myself.IPnode)
        print(" Para descargar y subir archivos abra otro cliente \n Pronto lo tendremos integrado")
        Myself.run()
    pass