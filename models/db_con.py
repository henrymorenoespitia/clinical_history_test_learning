PSQL_PASS="yourDBPassword"

PSQL_HOST="localhost"
PSQL_PORT="yourPort"
PSQL_USER="yourPostgresUser"
PSQL_DB="HistoriasClinicas"


import psycopg2


ruta_db= f"host={PSQL_HOST} port={PSQL_PORT} user={PSQL_USER} password={PSQL_PASS} dbname={PSQL_DB}"


###  ---  P A R A M E T R I Z A R  !!!  QUERIES ----  
def consulta_seleccion(sql, datos=None):
    sal = 'No hace nada en DB'
    #try:
    connection = psycopg2.connect(ruta_db)
    cursor=connection.cursor()
    #cursor.execute(sql)
    if datos == None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, datos)
    valores = cursor.fetchall()
    #connection.commit()
    cursor.close()
    connection.close()
    #print(valores)
    #except:
        #print("DB :: no se pudo conectar")
        #sal = None
    #return sal
    return valores
    

def consulta_accion(sql ): #, datos):
    exec = None
    sal = False
    #try:
    connection = psycopg2.connect(ruta_db)
    cursor=connection.cursor()
    #print(cursor.execute(sql, datos))
    try:
        exec = cursor.execute(sql)
        print("execute: ", exec)
        sal = True
    except:
        sal = False
    connection.commit()
    print("conection:", connection)
    cursor.close()
    connection.close()
    #except:
    #    print("DB :: no se pudo conectar o ejecutar la consulta")
    #    sal = None
    return sal



def verif_esta_hospital( nit_id, email ): # datos sanitizados
    # recibir parametro datos de la forma := ( nit_id, email )
    retornar = None
    #try:
    # parametrizados := ( nit_id, email )
    sql = f"""SELECT estado_activacion FROM public."oficial_hospital" WHERE  nit_id = '{nit_id}' AND email='{email}' ; """  #AND email = ? 
    #retornar = consulta_seleccion(sql, datos)
    retornar = consulta_seleccion(sql)
    #retornar = consulta_seleccion(sql)
    if retornar == None:
        print ('consulta no trajo nada o falla en PG')
    else:
        print(' consulta exitosa:: ', retornar)
    #except:
    #print('Query:: falla la verif_esta_hospital')
    return retornar
    

def cambio_estado_HOfic(nit_id, email, estado_nuevo): # recibir datos sanitizados
        #res = False
    #try:
        sql = f""" UPDATE  public."oficial_hospital" SET estado_activacion = '{estado_nuevo}' WHERE nit_id = '{nit_id}' AND email='{email}' ; """
        res = consulta_accion(sql)  # boolean
        print("respuesta en funcion cambio_estado_HOfic:: ", res)
    #except: 
        #res = False  
        #return res
        return res


def revertirRegistroHospital(nit_id, email):
    res = False
    #try:
    sql = f""" DELETE  public."Hospital" WHERE nit_id = '{nit_id}' AND email='{email}' ; """
    res = consulta_accion(sql)
    # adicionales:
    # -- añadir un Log para tener el registro de estos casos
    #except :
    #return res
    return res


# No solicitar id:: error de seguridad por probabilidad
def confirmarHospital(token):
    cambio_estado = 'A'
    sql = f"""UPDATE public."Hospital" SET vigen_tok='N' , token_ver='{token}' WHERE vigen_tok='S' AND token_ver='{token}'; """
    # mover el registro desde la tabla temporal hacia la tabla de Hospitales
    query_acc = consulta_accion(sql)
    if query_acc:
        pass
    else:
        print("no se ejecuto la consulta de actualizacion al confirmar token")
    return query_acc

    
def cargar_roles():
    print("paso por db")
    #sql="""SELECT id_user, roles FROM public.roles_por_users ;"""
    #resp = consulta_seleccion(sql)
    resp = {'123456': ['hos'], '654321':['med'] }

    #print("execucion de consulta roles:: ", resp)
    return resp


def validar_usuario(tipo_user, tipo_id, identif, password):
    if tipo_user == 'hos':
        sql=""" SELECT estado_activo, pwd FROM public."Hospital" WHERE nit_id='{identif}'; """
    elif tipo_user == 'med':
        sqle = """  ; """
    exec = consulta_seleccion(sql)
    print(exec)
    return True
    

def Paciente_reg_db(datos):
    retornar = ''
    #try:
    sql = 'INSERT INTO'
    resp = consulta_accion()
    if resp == None:
        print ('error en la consulta')
    else:
        pass
    #except: pass
    return retornar




"""def nuevo_hospital(nit_id, email, tel, estado_cambio, pwd, token_ver, vigen_tok): # recibir datos sanitizados !
    sql = f" INSERT INTO public.'Hospital' (nit_id, email, tel, estado_activo, pwd, token_ver, vigen_tok) VALUES ('{nit_id}', '{email}', '{tel}', '{estado_cambio}', '{pwd}', '{token_ver}', '{vigen_tok}'); "
    retornar = consulta_accion(sql)
    #print( "DB:: resultado de insercion:: ", retornar )
    #return retornar
    print("nuevo hospital:: ", retornar)
    return retornar
"""