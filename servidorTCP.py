import socket
import threading
import os
import os.path
import time
import hashlib
import math

#server_ip = '192.168.193.131'
host = input('Digite IP del servidor (Remoto: 192.168.193.131 Local: 127.0.0.1): ')
#port = 4752 (número aleatorio superior a 1024)
port = int(input('Digite puerto del servidor (4752): '))

clientes_paralelos = int(input('Digite el numero de clientes con el que compartira la conexion: '))
TAM_BUFFER = 1024
MAX_THREADS = 100
threads = []
dir_src = os.getcwd()
#carpeta para el almacenamiento de los archivos transmitidos. 
dir_data = os.path.join(dir_src,"data")
#carpeta para almacenar los archivos que se usarán de prueba.
dir_archivos = os.path.join(dir_src,"archivos")

# Se crea el socket de espera y se conecta el servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((host, port))
servidor.listen(5)

print ('Escuchando en (ip:puerto){}:{}'.format(host, port))

# Esta funcion es un thread que maneja la transferencia de archivos con un cliente.
def thread_conexion(socket__conexion_servidor_cliente, nombre_cliente, puerto_cliente):
    
    #se envia la lista de archivos primero
    os.chdir(dir_archivos)
    #esta linea envia un string. Toca codificarlo a un stream de bytes.
    socket__conexion_servidor_cliente.sendto('Hola'.encode(), (nombre_cliente, puerto_cliente))

    enviados = 0
    recibidos =0
    perdidos= 0
    tiempo_transcurrido = 0
    nombretxt = nombre_cliente + ".txt"

    #se recibe la peticion del archivo a enviar
    tiempo_inicio_conexion = time.time()
    peticion = socket__conexion_servidor_cliente.recv(TAM_BUFFER)

    while peticion != b'TERMINADA':
        os.chdir(dir_archivos)
        print ('Pidieron: {}'.format(peticion))
        
        #si la peticion no existe, espera una peticion correcta del cliente informando que no existe el archivo solicitado
        if not os.path.isfile(peticion):
            print('No existe')
            socket__conexion_servidor_cliente.sendto('No existe'.encode(), (nombre_cliente, puerto_cliente))
            peticion = socket__conexion_servidor_cliente.recv(TAM_BUFFER)

        #se debe enviar el tamano del archivo antes
        #con el tamano el cliente puede ver progreso y transferir correctamente los archivos
        tam_archivo = os.path.getsize(peticion)
        print('El archivo pedido {} tiene tamano {}'.format(peticion,tam_archivo))
        socket__conexion_servidor_cliente.sendto(str(tam_archivo).encode(), (nombre_cliente, puerto_cliente))

        if socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode() == 'OKTAM':
        
        #se abre el archivo que se quiere enviar, se lee en pedazos de tamano TAM_BUFFER
            tiempo_inicial = time.time()
            tiempo_inicial_str = time.strftime("%c")
            with open(peticion, 'rb') as f:
                archivo_enviar = f.read(TAM_BUFFER)
                
                #este while envia el archivo pedazo a pedazo hasta que ya no se lee mas.
                while archivo_enviar:
                    socket__conexion_servidor_cliente.send(archivo_enviar)
                    
                    if socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode() == 'OK':
                        #note que se envia a cada cliente un valor hash calculado para el archivo transmitido con el protocolo hash md5
                        archivo_enviar = hashlib.md5(archivo_enviar).hexdigest()
                        socket__conexion_servidor_cliente.send(archivo_enviar.encode())

                        if socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode() == 'OKHASH':
                            archivo_enviar = f.read(TAM_BUFFER)

        #se cierra el socket para escritura para prevenir errores
        tiempo_final = float(socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode())
        tiempo_final_server = time.time()
        tiempo_final_server_str = time.strftime("%c")
        tiempo_transcurrido = tiempo_final_server - tiempo_inicial
        print('Descarga finalizada con {}:{}'.format(nombre_cliente, puerto_cliente))

        socket__conexion_servidor_cliente.sendto(str(tiempo_transcurrido).encode(), (nombre_cliente, puerto_cliente))
        enviados = int(socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode())
        socket__conexion_servidor_cliente.sendto(str('d1').encode(), (nombre_cliente, puerto_cliente))
        recibidos = int(socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode())
        socket__conexion_servidor_cliente.sendto(str('d2').encode(), (nombre_cliente, puerto_cliente))
        perdidos= int(socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode())
        socket__conexion_servidor_cliente.sendto(str('d3').encode(), (nombre_cliente, puerto_cliente))
        corruptos= int(socket__conexion_servidor_cliente.recv(TAM_BUFFER).decode())
        socket__conexion_servidor_cliente.sendto(str('d4').encode(), (nombre_cliente, puerto_cliente))
        tiempo_total =time.time() - tiempo_inicio_conexion

        completa = "Yes"
        if recibidos*TAM_BUFFER < tam_archivo:
            completa = "No"
        os.chdir(dir_data)

        file = open(nombretxt,"a")
        file.write('Transferencia terminada. Inicio: {}. Fin: {}. Archivo: {}. Tamanio archivo: {}. Completo: {}. Total enviados: {}. Recibidos: {}. Corruptos: {}. Perdidos: {}. Tiempo envio: {}. Clientes al tiempo: {}\n'.format(tiempo_inicial_str, tiempo_final_server_str, peticion.decode(), str(tam_archivo) + " bytes", completa, enviados, recibidos, corruptos, perdidos, tiempo_transcurrido, clientes_paralelos))
        print('Transferencia terminada. Inicio: {}. Fin: {}. Archivo: {}. Tamanio archivo: {}. Completo: {}. Total enviados: {}. Recibidos: {}. Corruptos: {}. Perdidos: {}. Tiempo envio: {}. Clientes al tiempo: {}\n'.format(tiempo_inicial_str, tiempo_final_server_str, peticion.decode(), str(tam_archivo) + " bytes", completa, enviados, recibidos, corruptos, perdidos, tiempo_transcurrido, clientes_paralelos))
        file.close()
        
        #Siguiente peticion b'TERMINADA' o b'archivo'
        peticion = socket__conexion_servidor_cliente.recv(TAM_BUFFER)
    
    socket__conexion_servidor_cliente.shutdown(socket.SHUT_WR)
    print('Conexion cerrada con {}:{}.'.format(nombre_cliente, puerto_cliente))
    #se cierra el socket ahora si
    socket__conexion_servidor_cliente.close()

#####Esta funcion es un thread para la recepcion de multiples clientes.
def manejador_clientes():

    clientes_conectados = 0

    while clientes_conectados < clientes_paralelos:
        print('Esperando cliente numero ' + str(clientes_conectados+1))
        #se acepta conexion y se crea el socket de la comunicacion
        socket__conexion_servidor_cliente, direccion = servidor.accept()
        nombre_cliente = direccion[0]
        puerto_cliente = direccion[1]
        print ('Se acepto una conexion desde {}:{}'.format(direccion[0], direccion[1]))
        ##Esto inicia el threading de la comunicacion para un solo cliente
        e = threading.Event()

        if len(threads) < MAX_THREADS:
            thread_cliente = threading.Thread(
                target=thread_conexion,
                args=(socket__conexion_servidor_cliente, nombre_cliente, puerto_cliente,) 
            )
            threads.append(thread_cliente)

        clientes_conectados += 1

    #solo se inicia la transferencia de archivos cuando todos los clientes están listos
    for i in range(len(threads)):
        threads[i].start()

manejador_clientes()
