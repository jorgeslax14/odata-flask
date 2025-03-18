from flask import Flask, request, jsonify, Response, make_response
from flask_restful import Api, Resource
import xml.etree.ElementTree as ET
from flask_httpauth import HTTPBasicAuth
from urllib.parse import unquote
import re

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

# Usuarios autorizados (clave: usuario -> valor: contraseña)
USERS = {"admin": "admin", "usuario1": "admin123"}


@auth.verify_password
def verify_password(username, password):
    if username in USERS and USERS[username] == password:
        return username
    return None


# Base de datos simulada
# Datos simulados
PRODUCTOS = [
    {"ID": 1, "Nombre": "Producto A", "Precio": 100.5},
    {"ID": 2, "Nombre": "Producto B", "Precio": 200.0},
    {"ID": 3, "Nombre": "Producto C", "Precio": 150.75},
]


# Servicio OData para Productos
class ODataProductos(Resource):
    @auth.login_required
    def get(self):
        base_url = request.url_root.rstrip("/")
        filter_query = request.args.get("$filter", "")

        productos_filtrados = self.aplicar_filtro(filter_query, PRODUCTOS)

        response_data = {
            "@odata.context": f"{base_url}/odata/$metadata#Productos",
            "value": productos_filtrados
        }
        response = make_response(jsonify(response_data))
        response.headers["Content-Type"] = "application/json;odata.metadata=minimal"
        response.headers["OData-Version"] = "4.0"
        return response

    def aplicar_filtro(self, filter_query, productos):
        if not filter_query:
            return productos  # Sin filtro, devolver todos los productos
        
        try:
            filter_query = unquote(filter_query) 
            condiciones = self.parse_multiple_conditions(filter_query)

            productos_filtrados = productos
            for key, operator, value in condiciones:
                if key in ["ID", "Precio"]:
                    value = float(value) if "." in value else int(value)

                productos_filtrados = self.filtrar(productos_filtrados, key, operator, value)

            return productos_filtrados
        except Exception as e:
            print(f"Error aplicando filtro: {e}")
            return productos

    def parse_multiple_conditions(self, filter_query):
        pattern = r"(\w+)\s+(eq|ne|gt|lt|ge|le)\s+'?([\w\d.]+)'?"
        return re.findall(pattern, filter_query)

    def filtrar(self, productos, key, operator, value):
        if operator == "eq":
            return [p for p in productos if p[key] == value]
        elif operator == "ne":
            return [p for p in productos if p[key] != value]
        elif operator == "gt":
            return [p for p in productos if p[key] > value]
        elif operator == "lt":
            return [p for p in productos if p[key] < value]
        elif operator == "ge":
            return [p for p in productos if p[key] >= value]
        elif operator == "le":
            return [p for p in productos if p[key] <= value]
        return productos  # Si no se reconoce el operador, devolver sin filtrar

# Función para generar metadata.xml manualmente
def generate_metadata():

    edmx_namespace = "http://docs.oasis-open.org/odata/ns/edmx"
    edm_namespace = "http://docs.oasis-open.org/odata/ns/edm"

    edmx = ET.Element(f"{{{edmx_namespace}}}Edmx", Version="4.0")
    data_services = ET.SubElement(edmx, f"{{{edm_namespace}}}DataServices")

    # Schema
    schema = ET.SubElement(
        data_services, f"{{{edm_namespace}}}Schema", Namespace="ODataExample"
    )

    # Producto EntityType
    entity_type = ET.SubElement(
        schema, f"{{{edm_namespace}}}EntityType", Name="Producto"
    )
    key = ET.SubElement(entity_type, f"{{{edm_namespace}}}Key")
    ET.SubElement(key, f"{{{edm_namespace}}}PropertyRef", Name="ID")
    ET.SubElement(
        entity_type,
        f"{{{edm_namespace}}}Property",
        Name="ID",
        Type="Edm.Int32",
        Nullable="false",
    )
    ET.SubElement(
        entity_type,
        f"{{{edm_namespace}}}Property",
        Name="Nombre",
        Type="Edm.String",
    )
    ET.SubElement(
        entity_type,
        f"{{{edm_namespace}}}Property",
        Name="Precio",
        Type="Edm.Double",
    )

    # EntityContainer
    entity_container = ET.SubElement(
        schema, f"{{{edm_namespace}}}EntityContainer", Name="Container"
    )
    ET.SubElement(
        entity_container,
        f"{{{edm_namespace}}}EntitySet",
        Name="Productos",
        EntityType="ODataExample.Producto",
    )

    return ET.tostring(edmx, encoding="utf-8", method="xml").decode("utf-8")


# Servicio para exponer metadata OData
class MetadataService(Resource):
    @auth.login_required
    def get(self):
        metadata_xml = generate_metadata()
        response = Response(metadata_xml, mimetype="application/xml")
        response.headers["OData-Version"] = "4.0"
        return response


# Agregar rutas al API
api.add_resource(ODataProductos, "/odata/Productos")
api.add_resource(MetadataService, "/odata/$metadata")

if __name__ == "__main__":
    app.run(debug=True)
