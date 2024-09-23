from mailjet_rest import Client
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar Mailjet
mailjet = Client(auth=(os.getenv('MJ_APIKEY_PUBLIC'), os.getenv('MJ_APIKEY_PRIVATE')), version='v3.1')

def send_test_email():
    # Configuración del correo
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "soporte@sendiu.net",  # Cambia esto por tu correo electrónico
                    "Name": "Prueba Mailjet"
                },
                "To": [
                    {
                        "Email": "el_renyk_rmg@hotmail.com",  # Cambia esto por el correo del destinatario
                        "Name": "Destinatario"
                    }
                ],
                "Subject": "Correo de prueba desde Mailjet",
                "TextPart": "Este es un correo de prueba para verificar el envío a través de Mailjet.",
                "HTMLPart": "<h3>Este es un correo de prueba</h3><p>Hola, esto es un mensaje de prueba enviado desde Mailjet.</p>"
            }
        ]
    }
    
    # Enviar el correo
    result = mailjet.send.create(data=data)
    
    # Comprobar el resultado
    if result.status_code == 200:
        print("Correo enviado exitosamente!")
    else:
        print(f"Error al enviar el correo: {result.status_code}, {result.json()}")

if __name__ == "__main__":
    send_test_email()
