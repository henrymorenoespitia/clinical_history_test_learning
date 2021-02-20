
from flask import Flask, request, jsonify, Response
#import Flask-HTTPAuth
import models as model
import yagmail as yagmail ## temporal mientras se configura el servidor de correo
import os
import random

import secrets
import db_con as db
# SCRAM  -> si se cambia por SCRAM (cifrar contraseña cliente -> DB), no se podria hacer validacion
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt_claims, current_user
)


app = Flask(__name__)


rand_sec = os.urandom(24)
app.config['JWT_SECRET_KEY'] = rand_sec
jwt = JWTManager(app)


# Clase para utilizar con el JWT - ComplexObject que permite usar
#  los roles de usuario...
class UserObject:
    def __init__(self, id_user, roles):
        self.id_user = id_user
        self.roles = roles


def carga_roles_por_usuario():
    #print("paso por aca")
    roles_por_usuario = dict(db.cargar_roles())
    #print(roles_por_usuario)
    return roles_por_usuario


roles_por_usuario = carga_roles_por_usuario()
print("despues",roles_por_usuario) 


@jwt.user_loader_callback_loader
def user_loader_callback_loader(identity):
    if identity not in roles_por_usuario:
        return None

    return  UserObject(
        id_user=identity,
        roles=roles_por_usuario[identity]
    )


@app.route('/login', methods=['POST'])
def login():
    retornar = 'error...'
    if request.method == 'POST':
        if request.is_json:
            tipo_user = request.json['tipoUsuario']
            tipo_id = request.json['tipoDocumento']
            identif = request.json['identificacion']
            password = request.json['password']
        else:
            tipo_user = escape(request.form['tipoUsuario'])
            tipo_id = escape(request.form['tipoDocumento'])
            identif = escape(request.form['identificacion'])
            password = escape(request.form['password'])
        query_ex = db.validar_usuario(tipo_user, tipo_id, identif, password) # compara con check_password_hash
        if query_ex:
            try:
                access_token = create_access_token(identify=identif  )
                retornar = jsonify(message="Login exitoso", access_token=access_token)
            except:
                print('no se pudo crear el access_token')
                retornar = jsonify(message="Email o contrasena no valido(s)", access_token=access_token), 401
    else:
        pass

    return retornar


@app.route('/pruebaLogin/', methods=['POST'])
def pruebaLogin():
    if request.method == "POST":
        id_type = request.form['tipo_id']
        id = request.form['id']
        password = request.form['password']
        user_ = model.User_HC(id_type=id_type, id=id, password=password, user_type='hos')
        validate_access = user_.validate_access()
        if validate_access:
            print("acceso concedido")
            return jsonify({"message":"acceso SI"})
        return jsonify({"message":"accceso no"})


@app.route('/crearMedico/')
@jwt_required
def crearMedico():
    hospital_actual = get_jwt_identity()
    if 'hos' not in current_user.roles:
        print("este usuario no es un Hospital")
        return jsonify({"msg": "prohibido"}), 403
    else:
        print("si es un Hospital")
        return jsonify({"msg": "acceso concebido, rol hospital identificado"})
        
    ##  - logica algoritmica
    #  Validar:
    #           - Sea por user 'Hospital'
    #           - Validar ESCAPE datos no nullos ...
    return "no hago nada"



@app.route('/registrarHospital/', methods=['POST'])
def registrarrHospital():
    retornar = "  "
    if request.method == 'POST':
        nit_id   = str(escape( request.form['NIT']      )) ## colocar request.form.get -> esto para evitar generar el erro en caso de que no exista ete campo en el formulario
        email    = str(escape( request.form['email']    ))
        tel      = str(escape( request.form['telefono'] ))
        pwd      = escape(     request.form['clave']     )  # Ob.Mejora: recibir como array
        # !!! --- validar dentro del   M O D E L  : nulos, etc...  -- !!!
        print("email", email)
        email = email.upper()
        print("email", email)
        hashed_pwd  = generate_password_hash(pwd) 
        #datos_query = ( nit_id, email )
        is_verif_esta       =  db.verif_esta_hospital( nit_id, email )
        estado_activ        = 'I'                           # 'I': inactivo; 'P' := Pendiente-->falta por confirmar por correo o SMS!
        if is_verif_esta and is_verif_esta[0][0] == estado_activ:      # comprobar si es valido e inactivo
            print("Valido: esta inactivo: procede a registrar en tablaDB temporal y mandar correo para confirmar para anexar a la tablaDB de hospitales")
            token_ver = secrets.token_urlsafe( 256 )
            estado_cambio   = 'P'           # == pendiente por confirmar
            vigen_tok       = 'S'           # cambiar cuando sea utilizada la url por := 'N'
            hospital        = model.Hospital(nit_id=nit_id, email=email, telefono=tel, estado_activo=estado_cambio)
            resp            = hospital.saveNewHospital()    ###############
            print("insercion de nuevo hospital:", resp)
            if resp:
                mensaje_email = f"""Bienvenido, active su usuario haciendo ...  <a href= 'http://localhost:5000/confirmarHospital/{token_ver}'> click aqui \n </a>  <p> o copie el siguente enlace: \n http://localhost:5000/confirmarHospital/{token_ver} </p> """
                resp_email = enviarEmail(email, mensaje_email)
                if resp_email:
                    resp_cambio = db.cambio_estado_HOfic(nit_id, email, 'P')
                    if resp_cambio:
                        retornar =      jsonify(message='Hospital registrado con exito.'), 201
                    else:
                        print("error en cambio de estado de hospital para 'P' ... ") 
                        retornar=       jsonify(message='Error: verifique y modifique sus datos con la secretaria de salud.'), 502
                else:
                    # -- !! Bloquear en oficiales_h y deshacer la insercion en db
                    print(" -- ¡¡ bloquear hospital y deshacer la insercion en db !! -- ")
                    revertirRegistroHos = db.revertirRegistroHospital(nit_id, email)
                    if revertirRegistroHos:
                        print("error al revertir registro")
                        retornar =      jsonify(message='Error: verifique y modifique sus datos con la secretaria de salud.'), 502        
                    else:
                        retornar =      jsonify(message='Error: verifique y modifique sus datos con la secretaria de salud.'), 502        
        else:
            print("ya activo o no esta H. Validos")
            retornar =                  jsonify(message='Este hospital no se puede regitrar, cominiquese con el administador.'), 409  
    return retornar
     

@app.route('/confirmarHospital/<string:token>', methods=['GET'])
def confCorreoUsuario(token):
    retornar = jsonify(message="no se pudo confirmar su cuenta ...")
    if request.method == 'GET':
        respuesta_query = db.confirmarHospital(token)
        if respuesta_query:
            retornar = jsonify(message = "exito al confirmar"), 202
    return retornar



# Solo el registro porque necesita ser validada y authenticada la cuenta mediante cedula por el Sistema Hospitalario.
# p. 1 - crear Usuario:Paciente:
@app.route('/registrarPaciente/', methods=['POST'])
def registrarPaciente():
    if request.method=='POST':
        pass
    else:
        pass
    ##  - logica algoritmica
    # revisar si es hospital o 
    # Logs de intentos de acceso para mejorar sistema de seguridad
    return "crear Usuario 1"


@app.route('/confirmarUsuario/')
def confUser():
    ##  - Logica
    # validar 
    #         -que el usuario este en DB mediante el token
    # opcion de confirmar:
    # por Email o por SMS (para personas que no estan con cacapidad par ingresas al email)
    # 
    return False


@app.route('/confirmarCuentaMedico/')
def confirmarMedico():
    ##  - Logica
    # validar 
    #         - que el usuario este en DB mediante el token
    #         - solicitar confirmar por cedula y correo para contrastar
    return False


# por Usuairo Hospital, Paciente y Medico:
@app.route('/recuperarContrasena/')
def recuperarContrasena():
    return False


#generar contraseña de inicio para el medico
@app.route('/generarContrasenaMedico/')
def generarContrasenaMedico():
    pass
    return False


#consulta por parte del Medico que usara para leer y añadir datos a la historia clinica en CUALQUIER EVENTO atencion hospitalaria
@app.route('/historiaClinica')
def consultaHistClin():
    if request.method == 'Get':
        # realziar la validacion y consulta a la DB y retornar el objeto con los datos
        ## validar si no es un int en tal caso
        id = escape(request.args.get('id')) # string : CC TI RC *pasaporte *Extranjeria ... 
        #id = quitarEspacios(id)
        id = "Null"
        if id != "Null":
            pass
        else:
            pass
        return False
    elif request.method == 'POST':
        pass
    return False



"""@app.route('/historiaClinicaXMedico/<string:id>') #/<string:rango_Y_O_Fecha>', methods=['GET', 'POST'])
def consultaHistClin(id): #, rango_Y_O_Fecha):
    if request.method == 'Get':
        # realziar la validacion y consulta a la DB y retornar el objeto con los datos
        ## validar si no es un int en tal caso
        #id = escape(request.args.get('id')) # string : CC TI RC *pasaporte *Extranjeria ... 
        id = "null" #quitarEspacios(id)
        if id != "Null":
            pass
        else:
            pass
        #return False
    elif request.method == 'POST':
        pass
    return False
"""


def generarToken():
    token = secrets.token_urlsafe(256)
    return token


"""
@app.errorhandler(404)
def no_encontrado(error=None):
    response = jsonify( {
        'message': 'Recurso no encontrado' + request.url,
        'status': 404
    })
    response.status_code=404

    return response
"""

@app.route('/PruebaIngresoHospital', methods=['POST'])
def ingresoHospital():
    if request.method=='POST':
        nit_id   = str(escape( request.form['NIT']      ))
        email    = str(escape( request.form['email']    ))
        tel      = str(escape( request.form['telefono'] ))
        pwd      = escape(     request.form['clave']     )
        estado_cambio = 'P'
        token_ver = secrets.token_urlsafe( 256 )
        vigen_tok = 'S'
        resp = db.nuevo_hospital(nit_id, email, tel, estado_cambio, pwd, token_ver, vigen_tok)
        print("resp prueba ingres hospital:: ", resp)
    else:
        pass
    return jsonify(message = resp)


@app.route('/isVerificarHospital')
def PruRegHos():
    nit_id = '123456'
    email = 'qulque-email.COM'
    is_verif_esta =  db.verif_esta_hospital( nit_id, email )
    print("PRueba::: is_verif_hos :: ", is_verif_esta)
    return jsonify(message=is_verif_esta)


@app.route('/pruebaFail')
def pruebaFail():
    nit_id = '01235'
    email = 'quelque-email@GMAIL.COM'
    is_verif_esta = db.verif_esta_hospital( nit_id, email )
    print("tipo de la respuesta::: ", type(is_verif_esta))
    print("PRueba::: is_verif_hos :: ", is_verif_esta)
    return jsonify(message=is_verif_esta)


"""

@jwt.user_claims_loader
def add_claims_to_access_token(id_user):
    retornar = {'roles':carga_roles_por_usuario[id_user]}
    print("retonrar en claims_loadre:: ", retornar )
    return retornar


@jwt.user_identity_loader
def user_identity_loader(user_object):
    return user_object.id_user


@app.route('/prueba_Identidad_token/')
@jwt_required
def crearMedico():
    hospital_actual = get_jwt_identity()
    if 'ho' not in current_user.roles:
        retornar = {
            'identidad_actual': get_jwt_identity(),
            'roles_actuales': get_jwt_claims()['roles']
        }
        return jsonify(retornar), 200
    ##  - logica algoritmica
    #  Validar:
    #           - Sea por user 'Hospital'
    #           - Validar ESCAPE datos no nullos ...
    return "no hago nada"

"""

## split into another file inside /funciones 
def enviarEmail(email, mensaje):
    retornar = False
    try:
        yag = yagmail.SMTP(user="yourEmail", password="yourPassword")
        yag.send(to = email, subject= 'Historias-Clinicas: activacion --user--', contents=  mensaje)
        print("correo para confirmar  enviado con exito ")
        retornar = True
    except:
        retornar = False
    print("resultado en enviarEmail :: ", retornar)    
    return retornar


if __name__ == '__main__':
    app.run(debug=True)