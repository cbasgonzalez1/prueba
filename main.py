import os
import pandas as pd
import joblib
import uvicorn
import json
from fastapi import FastAPI
from pydantic import BaseModel


pathDeTrabajo='./'
pathModelos='modelos/'

columnas=pd.DataFrame(columns =['Temperatura','Genero','Secrecion Nasal','Congestion Nasal','Dolor garganta','Lagrimeo','Tos','Estornudos','Sensacion ahogo','Fiebre','dolor articular',
'Malestar general','Dolor cabeza','Picazon nasal','Hinchazon ojos','Ronquidos','Dolor muscular','Perdida voz','Dolor ojos','Diarrea','Nauseas',
'Dolor barriga','Dolor pecho','Perdida apetito','Escalofrios'])



import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


cred = credentials.Certificate(pathDeTrabajo+"asistentemedicovirtual-8f90ef98ec7e.json")
firebase_admin.initialize_app(cred)
db = firestore.client() # connecting to firestore


#---------Transformar datos a numericos---------------------------------------
def transformarDatos(datos):
    datos=pd.DataFrame([datos],columns=columnas.columns)
    print(datos)

    datos[datos == 'si'] = 1
    datos[datos == 'no'] = 0

    datos[datos == 'femenino'] = 1
    datos[datos == 'masculino'] = 0

    datos[datos == 'leve'] = 1
    datos[datos == 'moderado'] = 2
    datos[datos == 'fuerte'] = 3

    datos[datos == 'seca'] = 1
    datos[datos == 'con flema'] = 2
    print(datos)

    return datos



#Cargando modelo RF
if os.path.isfile(pathDeTrabajo+pathModelos+'Random-Forest.pkl'):  # Si existe
    modelRF = joblib.load(pathDeTrabajo+pathModelos+"Random-Forest.pkl")
else:
    print('El archivo: '+pathDeTrabajo+pathModelos+'Random-Forest.pkl no existe')
    exit
    
    
# Predice usando modelo
def predecir(datos):
    # Random Forest
    return modelRF.predict(datos[0:1]) 
    

#Armar Api
app = FastAPI()
    
class Sintomas(BaseModel):
    sintomas: list = []

@app.post("/predecir", status_code=201)
async def apiPrecedir(sintomas: Sintomas):
    datos = transformarDatos(sintomas.sintomas)
    diagnostico = predecir(datos.loc[:, datos.columns != 'Temperatura'])[0]
    guardarRegistro(datos,diagnostico)
    resp = {'estado':{'codigo':0,'mensaje':''},'payload': 'Diagnostico '+diagnostico+' Se recomienda acudir a un centro medico para confirmar el diagnostico y tratar oportunamente la enfermedad.'}
    return resp

@app.get("/", status_code=201)
async def getStatus():
    resp = {'estado':{'codigo':0,'mensaje':''},'payload':'OK'}
    return resp

@app.get("/temperatura", status_code=201)
async def getTemperatura():
    temp = obtenerUltimaTemperatura()
    resp = {'estado':{'codigo':0,'mensaje':''},'payload':temp}
    return resp
    
    
def guardarRegistro(datos,diagnostico):
    #Guardar datos en db
    datos['diagnostico']=diagnostico
    json = datos.to_dict(orient='index')[0]
    print(json)
    doc_ref = db.collection(u'prime_location').document()
    docId = doc_ref.id #generates id
    print('ID: ', docId) #print the generatd id
    collection = db.collection('sintomas')  # create collection
    res = collection.document(docId).set( json )
    print(res)

def obtenerUltimaTemperatura():
    collection = db.collection('temperatura')  # create collection
    res = collection.document('T').get().to_dict()
    print(res)
    return res['temp']
