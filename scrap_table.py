import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    # URL de la página web del IGP que contiene la información de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Realizar la solicitud HTTP a la página web
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    # Parsear el contenido HTML de la página web
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar la tabla de sismos en el HTML (asegúrate de ajustar el selector CSS a la estructura de la página)
    table = soup.find('table')  # Puede ser necesario ajustar este selector si la tabla tiene un id o clase específica
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.text.strip() for header in table.find_all('th')]

    # Extraer las filas de la tabla, limitando a los últimos 10 sismos
    rows = []
    for row in table.find_all('tr')[1:11]:  # Omitir el encabezado y limitar a las primeras 10 filas
        cells = row.find_all('td')
        row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells)}
        rows.append(row_data)

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismosIGP')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    # Insertar los nuevos datos
    for row in rows:
        row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
        table.put_item(Item=row)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
