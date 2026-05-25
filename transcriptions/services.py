import os
import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from google import genai
from google.genai.errors import APIError

def get_next_reset_time_bogota():
    """
    Calcula la próxima medianoche hora del Pacífico (cuando se restablece la cuota diaria de Gemini)
    y la convierte a la hora local correspondiente de Bogotá (America/Bogota).
    """
    pacific_tz = ZoneInfo('US/Pacific')
    bogota_tz = ZoneInfo('America/Bogota')
    
    # Obtener la hora actual en hora del Pacífico
    now_pacific = timezone.now().astimezone(pacific_tz)
    
    # Calcular la siguiente medianoche en hora del Pacífico
    next_midnight_pacific = datetime.datetime.combine(
        now_pacific.date() + datetime.timedelta(days=1),
        datetime.time.min,
        tzinfo=pacific_tz
    )
    
    # Convertir a hora de Bogotá
    next_reset_bogota = next_midnight_pacific.astimezone(bogota_tz)
    return next_reset_bogota.strftime("%I:%M %p")

def highlight_concepts_with_gemini(text: str) -> str:
    """
    Llama a la API de Gemini (gemini-1.5-flash) para identificar conceptos clave
    en el texto provisto y envolverlos en etiquetas HTML <mark>.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada en el servidor.")

    # Inicializar el cliente unificado de Gemini
    client = genai.Client(api_key=api_key)

    # Prompt estructurado
    prompt = (
        "Analiza el siguiente texto de una transcripción de clase. "
        "Identifica los conceptos, términos, fórmulas o definiciones más importantes y devuélveme el mismo texto "
        "pero envolviendo únicamente esos conceptos importantes en etiquetas HTML <mark>concepto</mark> (por ejemplo, <mark>fotosíntesis</mark>). "
        "No agregues explicaciones, resúmenes, ni bloques de código markdown, solo devuelve el texto original con las etiquetas añadidas."
        "\n\n"
        f"Texto: {text}"
    )

    # Realizar petición usando el nuevo SDK de GenAI
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    if not response or not response.text:
        raise ValueError("La respuesta de la API de Gemini está vacía.")
        
    return response.text.strip()
