import socket
import threading
import time
import os
import sys
import hashlib
import datetime 

TAM_BUFFER = 1024
lista_archivos = []
dir_src = os.getcwd()
dir_ArchivosRecibidos = os.path.join(dir_src,"ArchivosRecibidos")
dir_Logs= os.path.join(dir_src,"Logs")
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def cerrarConexion():
    try:
        servidor.sendto(b'TERMINADA',(nombre_servidor, puerto_servidor))
        servidor.shutdown(socket.SHUT_WR)
        servidor.close()
    except:
        print('No hay conexion')

def iniciarConexion(nombre_servidor0, puerto_servidor0):
    global lista_archivos
    global nombre_servidor
    global puerto_servidor

    nombre_servidor = nombre_servidor0
    puerto_servidor = puerto_servidor0

    name_archivo = input('Nombre del archivo a descargar:')

    print('Intentare conectarme a {}:{}'.format(nombre_servidor, puerto_servidor))
    servidor.connect((nombre_servidor, puerto_servidor))

    print('Conectado')

    saludo = servidor.recv(TAM_BUFFER)

    if saludo.decode() == 'Hola':
        print("Empieza transferencias")

    solicitar_archivos(name_archivo)

def solicitar_archivos(mensaje):
    print('Pedi {}'.format(mensaje))
    servidor.sendto(mensaje.encode(),(nombre_servidor, puerto_servidor))
    print('Mensaje enviado')
    tam_archivo = servidor.recv(TAM_BUFFER)
    servidor.sendto('OKTAM'.encode(),(nombre_servidor, puerto_servidor))
    print(tam_archivo)
    if not tam_archivo == b'No existe':
        tam_archivo = int(tam_archivo)
        print('Tamanio archivo: {}'.format(tam_archivo))
        tam_actual = 0
        buff = b""
        print('Recibiendo:')
        num_archivos = 0
        corruptos = 0
        os.chdir(dir_ArchivosRecibidos)
        with open(mensaje, 'wb') as f:
            while tam_actual < tam_archivo:

                archivo_recibir = servidor.recv(TAM_BUFFER)
                servidor.sendto('OK'.encode(),(nombre_servidor, puerto_servidor))
                hash_recibir = servidor.recv(TAM_BUFFER).decode()
                hash_object = hashlib.md5(archivo_recibir)
                servidor.sendto('OKHASH'.encode(),(nombre_servidor, puerto_servidor))
                num_archivos+=1

                if hash_object.hexdigest() == hash_recibir:

                    if not archivo_recibir:
                        break

                    if len(archivo_recibir) + tam_actual > tam_archivo:
                        archivo_recibir = archivo_recibir[:tam_archivo-tam_actual]
                    buff += archivo_recibir
                    tam_actual += len(archivo_recibir)
                    f.write(archivo_recibir)
                    progreso = (float(tam_actual)/float(tam_archivo))*100
                    print(str(progreso) + "%")

                else:
                    corruptos += 1


        tiempo_final = time.time()
        servidor.sendto(str(tiempo_final).encode(),(nombre_servidor, puerto_servidor))
        tiempo_transcurrido = str(servidor.recv(TAM_BUFFER).decode())
        tam_diferencia = tam_archivo - tam_actual
        perdidos = int(tam_diferencia/TAM_BUFFER)
        recibidos = num_archivos
        enviados = recibidos+perdidos

        servidor.sendto(str(enviados).encode(),(nombre_servidor, puerto_servidor))
        respuesta = str(servidor.recv(TAM_BUFFER).decode())
        if respuesta == 'YA':
            servidor.sendto(str(recibidos).encode(),(nombre_servidor, puerto_servidor))
        respuesta = str(servidor.recv(TAM_BUFFER).decode())
        if respuesta == 'YA':
            servidor.sendto(str(perdidos).encode(),(nombre_servidor, puerto_servidor))
        respuesta = str(servidor.recv(TAM_BUFFER).decode())
        if respuesta == 'YA':
            servidor.sendto(str(corruptos).encode(),(nombre_servidor, puerto_servidor))
        respuesta = str(servidor.recv(TAM_BUFFER).decode())

        if tam_diferencia == 0:
            stiempo = 'Recibido archivo completo. Tiempo transcurrido: {}. Bytes esperados: {}. Bytes recibidos: {}. Paquetes recibidos: {}. Paquetes corruptos: {}. Paquetes perdidos: {}. Paquetes enviados:{}'.format(tiempo_transcurrido,tam_archivo,tam_actual,num_archivos, corruptos, perdidos, enviados)
            print(stiempo)
            generarLog(mensaje,tam_archivo, nombre_servidor, 'Y', tiempo_transcurrido)
        else:
            stiempo = 'Recibido archivo incompleto. Tiempo transcurrido: {}. Bytes esperados: {}. Bytes recibidos: {}. Paquetes recibidos: {}. Paquetes corruptos: {}. Paquetes perdidos: {}. Paquetes enviados:{}'.format(tiempo_transcurrido,tam_archivo,tam_actual,num_archivos, corruptos, perdidos, enviados)
            print(stiempo)
    


def generarLog(nombre_archivo, tamanio, cliente, exito, tiempo): 
    datem = datetime.datetime.today()
    anio = datem.day 
    mes = datem.month      # 5
    dia = datem.year       # 2021
    hora = datem.hour       # 11
    min = datem.minute     # 22
    seg = datem.second     # 3
    nombre = str(anio) + str(mes) + str(dia) + str(hora) + str(min) + str(seg)  +'-Cliente'+'.txt'
    os.chdir(dir_Logs)
    with open(nombre, 'wb') as f:
        text = ''
        text +='Nombre de archivo {nom}\n'.format(nom=nombre_archivo)
        text += 'Tamaño archivo: {tam}\n'.format(tam = tamanio)
        text += 'Cliente: {cl}\n'.format(cl = cliente)
        text += 'Exitosa: {ex}\n'.format(ex = exito)
        text += 'Tiempo de transferencia: {t}\n'.format(t = tiempo)
        f.write(text.encode())



if __name__ == '__main__':
    print('Inicio:')
    nombre_servidor = input('Digite IP del servidor (Server: 192.168.193.131 Local: 127.0.0.1): ')
    puerto_servidor = int(input('Digite puerto del servidor (4752): '))
    iniciarConexion(nombre_servidor, puerto_servidor)
    print("Cerrare conexion")
    cerrarConexion()