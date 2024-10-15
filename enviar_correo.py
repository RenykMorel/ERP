import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# Credenciales de Mailjet
api_key = 'c5378b1317b394a5fc77d732701d5de3'
api_secret = '7a9c010dcca900504dba7410c3585a55'

# Datos del correo
data = {
    "Messages": [
        {
            "From": {
                "Email": "soporte@sendiu.net",
                "Name": "Renyk Morel"
            },
            "To": [
                {
                    "Email": "renyk.morel@sendiu.net",
                    "Name": "Prueba"
                }
            ],
            "Subject": "Asunto del correo",
            "TextPart": "Este es el contenido del correo en texto plano.",
            "HTMLPart": "<h3>Hola,</h3><p>Este es un ejemplo de correo enviado desde Mailjet por Renyk Morel.</p>",
            "CustomID": "AppTestEmail"
        }
    ]
}

# Enviar la solicitud a la API de Mailjet
response = requests.post(
    "https://api.mailjet.com/v3.1/send",
    auth=HTTPBasicAuth(api_key, api_secret),
    json=data
)

# Mostrar la respuesta
response_json = response.json()
if response.status_code == 200:
    print("Correo enviado exitosamente.")
else:
    print("Error al enviar el correo:", response.status_code)
    print(response_json)

# Guardar el cuerpo del correo en un archivo de texto
cuerpo_correo = "Hola,\nEste es un ejemplo de correo enviado desde Mailjet por Renyk Morel."
with open("cuerpo_correo.txt", "w", encoding="utf-8") as texto_file:
    texto_file.write(cuerpo_correo)

# Guardar un reporte del envío en un archivo CSV
reporte_data = {
    "Estado del envío": [response.status_code],
    "Respuesta de la API": [response_json],
    "Cuerpo del correo enviado": [cuerpo_correo]
}
reporte_df = pd.DataFrame(reporte_data)

# Cambiar la ruta del archivo CSV según sea necesario
reporte_csv = "reporte_envio.csv"
reporte_df.to_csv(reporte_csv, index=False, encoding='utf-8')
