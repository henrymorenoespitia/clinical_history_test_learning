
import db_con as db




class Hospital():
    def __init__(self,nit_id=None, email=None, estado_activo=None, nombre=None, direccion=None, servicios_ofrecidos=None, password=None, token_ver=None, vigencia_token=None,  telefono=None, Hospital_ID=None ):
        self.nit_id=nit_id
        self.email=email
        self.estado_activo=estado_activo
        self.nombre=nombre
        self.direccion=direccion
        self.servicios_ofrecidos=servicios_ofrecidos
        self.password=password
        self.token_ver=token_ver
        self.vigencia_token=None
        self.telefono=telefono
        self.Hospital_ID=Hospital_ID
    

# TODOS heredan de la clase User que tiene el metodo para el acceso (Login) de cada tipo de usuario
class User_HC():
    def __init__(self,user_type=None, id_type=None, id=None, password=None ):
        pass

    def validate_access(self):
        print("user_type: ", self.user_type)
        if self.user_type == 'hos':
            sql=""" SELECT FIRST estado_activo, pwd FROM public."Hospital" WHERE nit_id='{self.id}'; """
        elif self.user_type == 'med':
            sql = """  ; """
        exec = db.consulta_seleccion(sql)
        if exec:
            print(exec[0][1])
            ##validar PASSWORD
            pass
        print("resultado de validacion", exec)
        return True if (exec) else False


    def saveNewHospital(self):
        sql = f""" INSERT INTO public."Hospital" (nit_id, email, tel, estado_activo, pwd, token_ver, vigen_tok) VALUES ('{self.nit_id}', '{self.email}', '{self.telefono}', '{self.estado_activo}', '{self.password}', '{self.token_ver}', '{self.vigencia_token}'); """
        retornar = db.consulta_accion(sql)
        #print( "DB:: resultado de insercion:: ", retornar )
        #return retornar
        print("nuevo hospital:: ", retornar)
        return retornar


class Medico():
    pass


class Paciente():
    pass


class HistoriaClinica():
    pass

