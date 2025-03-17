from flask import Flask, request, jsonify, Response
from flask_restful import Api, Resource
import xml.etree.ElementTree as ET

app = Flask(__name__)
api = Api(app)

# Base de datos simulada
data_productos = [
    {"ID": 1, "Nombre": "Producto A", "Precio": 100.5},
    {"ID": 2, "Nombre": "Producto B", "Precio": 200.0}
]

data_personas = [
    {"ID": 1, "Nombre": "Juan Pérez", "Edad": 30},
    {"ID": 2, "Nombre": "Ana Gómez", "Edad": 25}
]

# Servicio OData para Productos
class ODataProductos(Resource):
    def get(self):
        return {
            "@odata.context": "https://odata-flask.onrender.com/odata/$metadata#Productos",
            "value": data_productos
        }, 200

    def post(self):
        try:
            new_entry = request.get_json()
            data_productos.append(new_entry)
            return {"message": "Producto agregado", "data": new_entry}, 201
        except Exception as e:
            return {"error": str(e)}, 400

# Servicio OData para Personas
class ODataPersonas(Resource):
    def get(self):
        return {"value": data_personas}, 200

    def post(self):
        try:
            new_entry = request.get_json()
            data_personas.append(new_entry)
            return {"message": "Persona agregada", "data": new_entry}, 201
        except Exception as e:
            return {"error": str(e)}, 400

# Función para generar metadata.xml manualmente
def generate_metadata():
    edm_namespace = "http://schemas.microsoft.com/ado/2008/09/edm"
    edmx_namespace = "http://schemas.microsoft.com/ado/2007/06/edmx"
    
    edmx = ET.Element(f"{{{edmx_namespace}}}Edmx", Version="1.0")
    data_services = ET.SubElement(edmx, f"{{{edmx_namespace}}}DataServices")
    
    schema = ET.SubElement(data_services, f"{{{edm_namespace}}}Schema", Namespace="ODataExample")

    # Entidad Producto
    entity_producto = ET.SubElement(schema, f"{{{edm_namespace}}}EntityType", Name="Producto")
    key = ET.SubElement(entity_producto, f"{{{edm_namespace}}}Key")
    ET.SubElement(key, f"{{{edm_namespace}}}PropertyRef", Name="ID")
    ET.SubElement(entity_producto, f"{{{edm_namespace}}}Property", Name="ID", Type="Edm.Int32")
    ET.SubElement(entity_producto, f"{{{edm_namespace}}}Property", Name="Nombre", Type="Edm.String")
    ET.SubElement(entity_producto, f"{{{edm_namespace}}}Property", Name="Precio", Type="Edm.Double")

    # Entidad Persona
    entity_persona = ET.SubElement(schema, f"{{{edm_namespace}}}EntityType", Name="Persona")
    key = ET.SubElement(entity_persona, f"{{{edm_namespace}}}Key")
    ET.SubElement(key, f"{{{edm_namespace}}}PropertyRef", Name="ID")
    ET.SubElement(entity_persona, f"{{{edm_namespace}}}Property", Name="ID", Type="Edm.Int32")
    ET.SubElement(entity_persona, f"{{{edm_namespace}}}Property", Name="Nombre", Type="Edm.String")
    ET.SubElement(entity_persona, f"{{{edm_namespace}}}Property", Name="Edad", Type="Edm.Int32")

    # Entity Container
    entity_container = ET.SubElement(schema, f"{{{edm_namespace}}}EntityContainer", Name="ODataExampleContainer")
    ET.SubElement(entity_container, f"{{{edm_namespace}}}EntitySet", Name="Productos", EntityType="ODataExample.Producto")
    ET.SubElement(entity_container, f"{{{edm_namespace}}}EntitySet", Name="Personas", EntityType="ODataExample.Persona")

    # Convertir XML a string
    return ET.tostring(edmx, encoding="utf-8", method="xml").decode("utf-8")

# Servicio para exponer metadata OData
class MetadataService(Resource):
    def get(self):
        metadata_xml = generate_metadata()
        return Response(metadata_xml, mimetype="application/xml")

# Agregar rutas al API
api.add_resource(ODataProductos, "/odata/productos")
api.add_resource(ODataPersonas, "/odata/personas")
api.add_resource(MetadataService, "/odata/$metadata")

if __name__ == "__main__":
    app.run(debug=True)
