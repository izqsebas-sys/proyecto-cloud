"""Script para generar el instructivo técnico del proyecto en PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ─── Colores del documento ────────────────────────────────────────────────────
NARANJA     = colors.HexColor("#E8650A")
AZUL_OSCURO = colors.HexColor("#1A2E4A")
GRIS_CLARO  = colors.HexColor("#F5F5F5")
GRIS_BORDE  = colors.HexColor("#CCCCCC")
VERDE       = colors.HexColor("#2E7D32")
AZUL_CLARO  = colors.HexColor("#E3F2FD")

# ─── Estilos ──────────────────────────────────────────────────────────────────
estilos = getSampleStyleSheet()

titulo_portada = ParagraphStyle("titulo_portada", fontSize=26, leading=32,
    textColor=AZUL_OSCURO, alignment=TA_CENTER, fontName="Helvetica-Bold")
subtitulo_portada = ParagraphStyle("subtitulo_portada", fontSize=14, leading=20,
    textColor=NARANJA, alignment=TA_CENTER, fontName="Helvetica")
info_portada = ParagraphStyle("info_portada", fontSize=11, leading=16,
    textColor=colors.HexColor("#444444"), alignment=TA_CENTER, fontName="Helvetica")

h1 = ParagraphStyle("h1", fontSize=16, leading=22, textColor=AZUL_OSCURO,
    fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8,
    borderPad=4, leftIndent=0)
h2 = ParagraphStyle("h2", fontSize=13, leading=18, textColor=NARANJA,
    fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
h3 = ParagraphStyle("h3", fontSize=11, leading=16, textColor=AZUL_OSCURO,
    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)

cuerpo = ParagraphStyle("cuerpo", fontSize=10, leading=15, alignment=TA_JUSTIFY,
    fontName="Helvetica", spaceAfter=6, textColor=colors.HexColor("#222222"))
cuerpo_bold = ParagraphStyle("cuerpo_bold", fontSize=10, leading=15,
    fontName="Helvetica-Bold", spaceAfter=4, textColor=AZUL_OSCURO)
codigo = ParagraphStyle("codigo", fontSize=9, leading=13, fontName="Courier",
    backColor=GRIS_CLARO, borderPad=6, leftIndent=12, spaceAfter=6,
    textColor=colors.HexColor("#333333"))
nota = ParagraphStyle("nota", fontSize=9, leading=13, fontName="Helvetica-Oblique",
    textColor=colors.HexColor("#555555"), leftIndent=12, spaceAfter=4)

def hr():
    return HRFlowable(width="100%", thickness=1, color=GRIS_BORDE, spaceAfter=6)

def seccion(titulo):
    return [Paragraph(titulo, h1), hr()]

def subseccion(titulo):
    return [Paragraph(titulo, h2)]

def p(texto):
    return Paragraph(texto, cuerpo)

def bold(texto):
    return Paragraph(texto, cuerpo_bold)

def cod(texto):
    return Paragraph(texto, codigo)

def tabla_tecnologia(filas, col_anchos=None):
    if col_anchos is None:
        col_anchos = [4*cm, 3.5*cm, 9*cm]
    encabezados = [
        Paragraph("<b>Tecnología</b>", ParagraphStyle("th", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Versión / Tier</b>", ParagraphStyle("th", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Justificación</b>", ParagraphStyle("th", fontSize=10, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
    ]
    datos = [encabezados] + filas
    t = Table(datos, colWidths=col_anchos)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
        ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("FONTSIZE", (0,1), (-1,-1), 9),
    ]))
    return t

def tabla_comparacion(filas):
    col_anchos = [4*cm, 4.5*cm, 4.5*cm, 3.5*cm]
    encabezados = [
        Paragraph("<b>Práctica</b>", ParagraphStyle("th2", fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Tecnología</b>", ParagraphStyle("th2", fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Qué aprendimos</b>", ParagraphStyle("th2", fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph("<b>Uso en el Proyecto</b>", ParagraphStyle("th2", fontSize=9, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER)),
    ]
    datos = [encabezados] + filas
    t = Table(datos, colWidths=col_anchos)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F8E9")]),
        ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("FONTSIZE", (0,1), (-1,-1), 9),
    ]))
    return t

# ─── Construcción del documento ───────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/Users/sebasizq/Documents/CLOUD/proyecto/Instructivo_Proyecto_Cloud.pdf",
    pagesize=A4,
    rightMargin=2.2*cm, leftMargin=2.2*cm,
    topMargin=2.5*cm, bottomMargin=2.5*cm
)

contenido = []

# ══════════════════════════════════════════════════════════════════════════════
# PORTADA
# ══════════════════════════════════════════════════════════════════════════════
contenido += [
    Spacer(1, 3*cm),
    Paragraph("INSTRUCTIVO TÉCNICO", subtitulo_portada),
    Spacer(1, 0.4*cm),
    Paragraph("Sistema de Pedidos Asíncronos", titulo_portada),
    Spacer(1, 0.3*cm),
    Paragraph("API REST · RabbitMQ · PostgreSQL · HAProxy · AWS EC2 · Terraform", subtitulo_portada),
    Spacer(1, 2*cm),
    HRFlowable(width="80%", thickness=2, color=NARANJA, spaceAfter=20),
    Spacer(1, 0.5*cm),
    Paragraph("Computación en la Nube — Proyecto Final", info_portada),
    Paragraph("Pontificia Universidad Javeriana Cali", info_portada),
    Spacer(1, 0.3*cm),
    Paragraph("Sebastián Izquierdo  ·  izqsebas@gmail.com", info_portada),
    Spacer(1, 0.3*cm),
    Paragraph("Mayo 2026", info_portada),
    Spacer(1, 3*cm),
    HRFlowable(width="80%", thickness=1, color=GRIS_BORDE),
    Spacer(1, 0.5*cm),
    Paragraph(
        "Repositorio: <font color='#1A2E4A'>github.com/izqsebas-sys/proyecto-cloud</font>  ·  "
        "Swagger UI en producción: <font color='#1A2E4A'>http://100.54.28.154/docs</font>",
        info_portada),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════════════════════════
# 1. RESUMEN EJECUTIVO
# ══════════════════════════════════════════════════════════════════════════════
contenido += seccion("1. Resumen Ejecutivo")
contenido += [
    p("Este proyecto implementa un <b>sistema de procesamiento de pedidos asíncrono</b> "
      "desplegado completamente en AWS usando infraestructura como código (IaC) con Terraform. "
      "El sistema combina todas las tecnologías estudiadas durante el semestre — Docker, "
      "Python, RabbitMQ, PostgreSQL, HAProxy y AWS — en una solución de producción real."),
    Spacer(1, 0.3*cm),
    p("La arquitectura separa claramente las responsabilidades: la <b>API</b> recibe peticiones "
      "y las encola, el <b>Worker</b> las procesa en segundo plano, y el <b>balanceador HAProxy</b> "
      "distribuye el tráfico entre dos instancias de la API para garantizar disponibilidad."),
    Spacer(1, 0.4*cm),
]

# Tabla resumen de componentes
datos_resumen = [
    [Paragraph("<b>Componente</b>", cuerpo_bold), Paragraph("<b>Instancias</b>", cuerpo_bold),
     Paragraph("<b>Función</b>", cuerpo_bold)],
    [Paragraph("HAProxy", cuerpo), Paragraph("1 EC2", cuerpo),
     Paragraph("Balanceador de carga, único punto de entrada público (puerto 80)", cuerpo)],
    [Paragraph("FastAPI (API)", cuerpo), Paragraph("2 EC2", cuerpo),
     Paragraph("Recibe pedidos, los valida, los guarda en BD y los encola en RabbitMQ", cuerpo)],
    [Paragraph("RabbitMQ", cuerpo), Paragraph("1 EC2", cuerpo),
     Paragraph("Broker de mensajes, desacopla la API del Worker", cuerpo)],
    [Paragraph("Worker Python", cuerpo), Paragraph("1 EC2", cuerpo),
     Paragraph("Consume las colas y ejecuta las operaciones en PostgreSQL", cuerpo)],
    [Paragraph("PostgreSQL", cuerpo), Paragraph("1 EC2", cuerpo),
     Paragraph("Base de datos relacional, almacena pedidos y tareas", cuerpo)],
    [Paragraph("AWS SSM", cuerpo), Paragraph("Servicio", cuerpo),
     Paragraph("Almacén de configuración centralizado para IPs y parámetros", cuerpo)],
]
t = Table(datos_resumen, colWidths=[4*cm, 3*cm, 9.5*cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
contenido.append(t)
contenido.append(Spacer(1, 0.3*cm))

# ══════════════════════════════════════════════════════════════════════════════
# 2. ARQUITECTURA DEL SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("2. Arquitectura del Sistema")
contenido += [
    p("El sistema sigue un patrón de <b>arquitectura basada en eventos</b>. Las operaciones "
      "que pueden tomar tiempo (crear o eliminar un pedido) se ejecutan de forma asíncrona "
      "a través de RabbitMQ, mientras que las operaciones rápidas (listar, actualizar) son síncronas."),
    Spacer(1, 0.4*cm),
]

contenido += subseccion("2.1 Diagrama de Flujo Asíncrono (Creación de Pedido)")
contenido += [
    cod("Cliente  →  HAProxy (puerto 80)  →  API-1 o API-2 (puerto 8000)"),
    cod("   API  →  PostgreSQL: INSERT en tabla 'tasks' (estado: pendiente)"),
    cod("   API  →  RabbitMQ: publicar en cola 'orders_create'"),
    cod("   API  →  Cliente: HTTP 202 + task_id"),
    cod(""),
    cod("Worker  ←  RabbitMQ: consumir mensaje de 'orders_create'"),
    cod("Worker  →  PostgreSQL: INSERT en tabla 'orders'"),
    cod("Worker  →  PostgreSQL: UPDATE tasks SET estado='completado'"),
    cod(""),
    cod("Cliente  →  GET /tasks/{task_id}  →  verifica cuando estado='completado'"),
    Spacer(1, 0.3*cm),
    p("Este patrón se conoce como <b>polling de estado</b>: el cliente pregunta periódicamente "
      "hasta que la tarea se completa. Es simple de implementar y no requiere websockets ni "
      "notificaciones push."),
    Spacer(1, 0.3*cm),
]

contenido += subseccion("2.2 Flujo Síncrono (Actualización de Pedido)")
contenido += [
    cod("Cliente  →  HAProxy  →  API  →  PostgreSQL: UPDATE directo  →  HTTP 200"),
    Spacer(1, 0.2*cm),
    p("La actualización es síncrona porque es una operación rápida (un UPDATE en BD) "
      "que no requiere procesamiento adicional por parte del Worker."),
    Spacer(1, 0.3*cm),
]

contenido += subseccion("2.3 Comunicación entre Servicios vía SSM")
contenido += [
    p("En el Learner Lab de AWS Academy las IPs de las instancias cambian con cada sesión. "
      "Para solucionar esto, Terraform guarda las IPs privadas en <b>AWS SSM Parameter Store</b> "
      "al momento de crear la infraestructura. La API y el Worker las leen al arrancar usando "
      "el SDK boto3."),
    Spacer(1, 0.2*cm),
    cod("/proyecto/postgres_host  →  IP privada de la instancia PostgreSQL"),
    cod("/proyecto/rabbitmq_host  →  IP privada de la instancia RabbitMQ"),
    cod("/proyecto/haproxy_ip     →  IP pública del balanceador HAProxy"),
    Spacer(1, 0.3*cm),
]

# ══════════════════════════════════════════════════════════════════════════════
# 3. PROGRESIÓN DEL CURSO — CÓMO CADA PRÁCTICA LLEVÓ AL PROYECTO FINAL
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("3. Progresión del Curso: De las Prácticas al Proyecto Final")
contenido += [
    p("El proyecto final no surgió de la nada. Cada práctica del semestre introdujo "
      "una tecnología o concepto que luego se integró en la solución final. "
      "La siguiente tabla muestra esa progresión:"),
    Spacer(1, 0.4*cm),
]

filas_prog = [
    [Paragraph("0. Dev Environment", cuerpo),
     Paragraph("Docker + Dockerfile", cuerpo),
     Paragraph("Crear imágenes reproducibles sin depender del SO del desarrollador", cuerpo),
     Paragraph("API y Worker corren en contenedores Docker en cada EC2", cuerpo)],

    [Paragraph("Practice 1\nHTML + Docker", cuerpo),
     Paragraph("Contenedor web básico", cuerpo),
     Paragraph("Empaquetar una aplicación en un contenedor y exponerla en un puerto", cuerpo),
     Paragraph("Base para entender cómo Docker expone servicios al exterior", cuerpo)],

    [Paragraph("Practice 3\nFlask + Redis", cuerpo),
     Paragraph("Flask, Redis, docker-compose", cuerpo),
     Paragraph("API web con estado persistente, múltiples servicios en red", cuerpo),
     Paragraph("Flask → FastAPI. Redis (caché) → PostgreSQL (persistencia real)", cuerpo)],

    [Paragraph("Practice 4\nRabbitMQ", cuerpo),
     Paragraph("pika, colas AMQP, fanout exchange", cuerpo),
     Paragraph("Publicar y consumir mensajes, desacoplar productores de consumidores", cuerpo),
     Paragraph("Patrón exacto usado entre la API (producer) y el Worker (consumer)", cuerpo)],

    [Paragraph("Lab 1\nAWS Lambda básico", cuerpo),
     Paragraph("AWS Lambda, AWS CLI, zip deploy", cuerpo),
     Paragraph("Primer contacto con AWS, credenciales, despliegue serverless", cuerpo),
     Paragraph("Familiarización con AWS y boto3, base para usar SSM", cuerpo)],

    [Paragraph("Lab 3\nLambda + EC2", cuerpo),
     Paragraph("EC2, Lambda, AWS CLI", cuerpo),
     Paragraph("Crear instancias EC2 y conectar Lambda con recursos de red", cuerpo),
     Paragraph("EC2 es el modelo de cómputo del proyecto final (IaaS)", cuerpo)],

    [Paragraph("Lab 4\nLambda + S3", cuerpo),
     Paragraph("S3, Terraform básico, IaC", cuerpo),
     Paragraph("Infraestructura como código: describir recursos en archivos .tf", cuerpo),
     Paragraph("Terraform escala al proyecto: 6 EC2 + security groups + SSM con un solo apply", cuerpo)],

    [Paragraph("Lab 6\nLambda + DynamoDB", cuerpo),
     Paragraph("DynamoDB, Lambda múltiples funciones, simulador IoT", cuerpo),
     Paragraph("Patrón ingesta + consulta, arquitectura de múltiples componentes", cuerpo),
     Paragraph("Motivó usar PostgreSQL (relacional) en lugar de DynamoDB para el proyecto", cuerpo)],

    [Paragraph("aws-iaas-examples\nALB, RabbitMQ+PostgreSQL", cuerpo),
     Paragraph("ALB, HAProxy, SSM Parameter Store, múltiples EC2", cuerpo),
     Paragraph("Balanceadores de carga, configuración centralizada con SSM, instalación automatizada", cuerpo),
     Paragraph("Template directo del proyecto: mismo patrón de install_*.sh y SSM", cuerpo)],
]
contenido.append(tabla_comparacion(filas_prog))
contenido.append(Spacer(1, 0.3*cm))

# ══════════════════════════════════════════════════════════════════════════════
# 4. JUSTIFICACIÓN DE TECNOLOGÍAS
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("4. Justificación de Tecnologías y Librerías")

# 4.1 Python
contenido += subseccion("4.1 Python 3.x — Lenguaje Principal")
contenido += [
    p("Python fue el lenguaje usado en todas las prácticas del curso (Lambda, Flask, pika, boto3). "
      "Su ecosistema de librerías para nube (boto3), mensajería (pika) y bases de datos (psycopg2) "
      "cubre exactamente lo que necesita el proyecto. No fue necesario aprender un lenguaje nuevo."),
    Spacer(1, 0.2*cm),
]

# 4.2 FastAPI
contenido += subseccion("4.2 FastAPI — Framework Web de la API")
filas_fastapi = [
    [Paragraph("FastAPI", cuerpo),
     Paragraph("0.115.x", cuerpo),
     Paragraph("Framework web moderno de Python. Genera automáticamente la documentación "
               "Swagger UI (/docs), valida los datos de entrada con Pydantic sin código extra, "
               "y es considerablemente más rápido que Flask (usado en Practice 3). "
               "La validación automática de tipos previene errores de datos sin escribir "
               "código de validación manual.", cuerpo)],
    [Paragraph("Uvicorn", cuerpo),
     Paragraph("ASGI server", cuerpo),
     Paragraph("Servidor de producción para FastAPI. Es el equivalente a Gunicorn pero "
               "para aplicaciones ASGI (asíncronas). Se especifica en el Dockerfile como "
               "comando de arranque.", cuerpo)],
    [Paragraph("Pydantic", cuerpo),
     Paragraph("Incluida en FastAPI", cuerpo),
     Paragraph("Valida automáticamente el JSON recibido contra los modelos OrderCreate y "
               "OrderUpdate. Si el cliente envía un campo inválido, FastAPI retorna un "
               "error 422 descriptivo sin necesidad de código adicional.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_fastapi))
contenido.append(Spacer(1, 0.3*cm))

# 4.3 RabbitMQ
contenido += subseccion("4.3 RabbitMQ + pika — Mensajería Asíncrona")
contenido += [
    p("RabbitMQ se introdujo en la <b>Práctica 4</b> donde se aprendió a publicar y consumir "
      "mensajes con el patrón fanout (broadcast). En el proyecto se usa el patrón más simple "
      "de <b>cola directa</b> (direct queue): un mensaje va a una cola específica y un solo "
      "Worker lo procesa."),
    Spacer(1, 0.2*cm),
    p("<b>¿Por qué RabbitMQ y no SQS de AWS?</b> El Learner Lab tiene permisos limitados "
      "para crear servicios adicionales de AWS. Además, RabbitMQ se estudió explícitamente "
      "en el curso y su instalación con Docker es directa. En producción real se usaría "
      "Amazon SQS por ser administrado y no requerir mantenimiento."),
    Spacer(1, 0.2*cm),
]
filas_rabbit = [
    [Paragraph("pika", cuerpo),
     Paragraph("1.3.x", cuerpo),
     Paragraph("Librería oficial de Python para el protocolo AMQP (el protocolo de RabbitMQ). "
               "Usada en Practice 4. Permite publicar mensajes desde la API y consumirlos "
               "en el Worker con callbacks.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_rabbit))
contenido.append(Spacer(1, 0.3*cm))

# 4.4 PostgreSQL
contenido += subseccion("4.4 PostgreSQL — Base de Datos Relacional")
contenido += [
    p("PostgreSQL se introdujo en los laboratorios de EC2 con el script "
      "<i>ec2-user-data-postgresql.sh</i> y en los ejemplos de IaaS. "
      "Se eligió PostgreSQL sobre otras alternativas por las siguientes razones:"),
    Spacer(1, 0.1*cm),
]
filas_pg = [
    [Paragraph("PostgreSQL", cuerpo),
     Paragraph("15.x", cuerpo),
     Paragraph("Base de datos relacional con soporte nativo para JSONB (JSON Binario). "
               "El campo 'payload' de los pedidos se almacena como JSONB, lo que permite "
               "actualizar campos individuales con el operador '||' sin reescribir todo el "
               "objeto. Esto hace el endpoint PUT eficiente y flexible.", cuerpo)],
    [Paragraph("psycopg2", cuerpo),
     Paragraph("2.9.x", cuerpo),
     Paragraph("Conector Python para PostgreSQL. Es el estándar de la industria. "
               "Usa consultas parametrizadas (%s) que previenen inyección SQL automáticamente.", cuerpo)],
    [Paragraph("pgcrypto", cuerpo),
     Paragraph("Extensión PostgreSQL", cuerpo),
     Paragraph("Extensión habilitada en el script de instalación para soporte de UUIDs "
               "nativos en la base de datos. Las tablas 'tasks' y 'orders' usan UUID como "
               "clave primaria en lugar de enteros secuenciales.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_pg))
contenido.append(Spacer(1, 0.2*cm))
contenido += [
    p("<b>¿Por qué PostgreSQL y no DynamoDB?</b> En el Lab 6 se estudió DynamoDB, "
      "que es excelente para datos sin esquema fijo y alta escala. Sin embargo, el proyecto "
      "tiene relaciones claras entre tablas (tasks ↔ orders mediante foreign key) y necesita "
      "transacciones ACID para garantizar consistencia. PostgreSQL es la herramienta correcta "
      "para datos estructurados con relaciones."),
    Spacer(1, 0.3*cm),
]

# 4.5 HAProxy
contenido += [PageBreak()]
contenido += subseccion("4.5 HAProxy — Balanceador de Carga")
contenido += [
    p("HAProxy se estudió en la carpeta <i>balancers/</i> y en los ejemplos "
      "<i>aws-iaas-examples/aws-iaas-alb/</i>. Se eligió HAProxy sobre el "
      "Application Load Balancer (ALB) de AWS porque:"),
    Spacer(1, 0.1*cm),
]
filas_ha = [
    [Paragraph("HAProxy", cuerpo),
     Paragraph("2.8.x (Docker)", cuerpo),
     Paragraph("Balanceador de carga open source. Distribuye las peticiones entre API-1 y "
               "API-2 con el algoritmo round-robin (alterna entre servidores). Si una API "
               "falla, HAProxy deja de enviarle tráfico automáticamente. "
               "El Learner Lab tiene permisos limitados para crear ALBs pagos, "
               "mientras que HAProxy corre gratis en una EC2 t3.micro.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_ha))
contenido.append(Spacer(1, 0.3*cm))

# 4.6 Docker
contenido += subseccion("4.6 Docker — Contenerización de la API y el Worker")
filas_docker = [
    [Paragraph("Docker", cuerpo),
     Paragraph("24.x", cuerpo),
     Paragraph("La API y el Worker corren en contenedores Docker dentro de sus EC2. "
               "Esto garantiza que el entorno de ejecución es idéntico al de desarrollo "
               "(el mismo Dockerfile, las mismas dependencias). Sin Docker, habría que "
               "instalar Python, pip y cada librería manualmente en cada instancia.", cuerpo)],
    [Paragraph("Dockerfile", cuerpo),
     Paragraph("Multi-stage no requerido", cuerpo),
     Paragraph("Cada componente (api/, worker/) tiene su propio Dockerfile que parte de "
               "python:3.11-slim, instala requirements.txt y define el comando de arranque. "
               "python:3.11-slim se eligió sobre python:3.11 porque ocupa menos espacio en disco.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_docker))
contenido.append(Spacer(1, 0.3*cm))

# 4.7 Terraform
contenido += subseccion("4.7 Terraform — Infraestructura como Código (IaC)")
contenido += [
    p("Terraform se introdujo en el <b>Lab 4 (Lambda + S3)</b> donde se aprendió a definir "
      "recursos en archivos .tf y aplicarlos con <i>terraform apply</i>. En el proyecto, "
      "Terraform gestiona 9 recursos de AWS con un solo comando:"),
    cod("terraform apply -auto-approve"),
    Spacer(1, 0.1*cm),
]
filas_tf = [
    [Paragraph("Terraform", cuerpo),
     Paragraph("≥ 1.11 / OpenTofu", cuerpo),
     Paragraph("Define los 6 EC2, los 5 security groups y los 3 parámetros SSM como código. "
               "Permite destruir y recrear toda la infraestructura en minutos. "
               "Compatible con OpenTofu (fork open source de Terraform), usado en los "
               "laboratorios del curso.", cuerpo)],
    [Paragraph("templatefile()", cuerpo),
     Paragraph("Función de Terraform", cuerpo),
     Paragraph("Inyecta variables (IP de la API, contraseña de BD, URL del repo) en los "
               "scripts bash de instalación. Evita hardcodear valores que cambian entre "
               "sesiones del Learner Lab.", cuerpo)],
    [Paragraph("AWS SSM\nParameter Store", cuerpo),
     Paragraph("Servicio AWS", cuerpo),
     Paragraph("Terraform guarda las IPs privadas de PostgreSQL y RabbitMQ en SSM después "
               "de crear las instancias. La API y el Worker las leen con boto3 al arrancar. "
               "Soluciona el problema de que las IPs cambian con cada sesión del Learner Lab.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_tf))
contenido.append(Spacer(1, 0.3*cm))

# 4.8 boto3
contenido += subseccion("4.8 boto3 — SDK de AWS para Python")
filas_boto = [
    [Paragraph("boto3", cuerpo),
     Paragraph("1.34.x", cuerpo),
     Paragraph("SDK oficial de AWS para Python. Se usa para leer los parámetros de SSM "
               "desde la API, el Worker y el Producer. Sin boto3 habríamos tenido que "
               "hacer llamadas HTTP manuales a la API de SSM con autenticación compleja. "
               "boto3 maneja automáticamente la autenticación con los credenciales del "
               "perfil de instancia IAM (LabInstanceProfile).", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_boto))
contenido.append(Spacer(1, 0.3*cm))

# 4.9 Herramientas de calidad
contenido += subseccion("4.9 pytest y ruff — Calidad de Código")
filas_qa = [
    [Paragraph("pytest", cuerpo),
     Paragraph("8.3.x", cuerpo),
     Paragraph("Framework de pruebas unitarias. Los 17 tests cubren todos los endpoints "
               "de la API usando mocks para PostgreSQL y RabbitMQ. Esto permite verificar "
               "la lógica de la API sin necesidad de tener las bases de datos corriendo.", cuerpo)],
    [Paragraph("ruff", cuerpo),
     Paragraph("0.x", cuerpo),
     Paragraph("Linter y formateador de Python extremadamente rápido (escrito en Rust). "
               "Detecta imports sin usar, imports desordenados y problemas de estilo. "
               "Se configura en pyproject.toml para aplicar las mismas reglas a todos "
               "los módulos del proyecto.", cuerpo)],
    [Paragraph("unittest.mock", cuerpo),
     Paragraph("Librería estándar Python", cuerpo),
     Paragraph("Permite reemplazar las conexiones reales a PostgreSQL y RabbitMQ con "
               "objetos falsos (MagicMock) durante las pruebas. Así los tests son rápidos "
               "y no dependen de infraestructura externa.", cuerpo)],
]
contenido.append(tabla_tecnologia(filas_qa))

# ══════════════════════════════════════════════════════════════════════════════
# 5. ESTRUCTURA DEL PROYECTO
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("5. Estructura del Repositorio")
contenido += [
    cod("proyecto/"),
    cod("├── api/"),
    cod("│   ├── main.py              ← API REST (FastAPI): endpoints, validación, lógica"),
    cod("│   ├── requirements.txt     ← Dependencias Python de la API"),
    cod("│   ├── Dockerfile           ← Imagen Docker de la API"),
    cod("│   └── tests/"),
    cod("│       ├── conftest.py      ← Configuración de fixtures para pytest"),
    cod("│       └── test_main.py     ← 17 tests unitarios de todos los endpoints"),
    cod("├── worker/"),
    cod("│   ├── worker.py            ← Consumidor RabbitMQ: crea y elimina pedidos en BD"),
    cod("│   ├── requirements.txt     ← Dependencias Python del Worker"),
    cod("│   └── Dockerfile           ← Imagen Docker del Worker"),
    cod("├── producer/"),
    cod("│   ├── producer.py          ← Generador sintético de pedidos para pruebas de carga"),
    cod("│   └── requirements.txt     ← Dependencias del Producer"),
    cod("├── terraform/"),
    cod("│   ├── main.tf              ← 6 EC2 + 3 parámetros SSM"),
    cod("│   ├── security_groups.tf   ← Reglas de firewall por servicio"),
    cod("│   ├── variables.tf         ← VPC, subnet, AMI, key pair, repo URL"),
    cod("│   ├── providers.tf         ← Proveedor AWS, región us-east-1"),
    cod("│   ├── outputs.tf           ← IPs y URLs que se muestran al hacer apply"),
    cod("│   ├── install_postgres.sh  ← Instala PostgreSQL, crea BD y tablas"),
    cod("│   ├── install_rabbitmq.sh  ← Instala RabbitMQ con Docker"),
    cod("│   ├── install_api.sh       ← Clona repo, construye y corre contenedor API"),
    cod("│   ├── install_haproxy.sh   ← Instala HAProxy con IPs de las APIs"),
    cod("│   ├── install_worker.sh    ← Clona repo, construye y corre contenedor Worker"),
    cod("│   └── Makefile             ← Atajos: make apply, make destroy"),
    cod("├── pyproject.toml           ← Configuración de ruff (linter)"),
    cod("├── .gitignore               ← Excluye __pycache__, .env, .claude/"),
    cod("└── README.md                ← Instrucciones de despliegue y uso"),
    Spacer(1, 0.3*cm),
]

# ══════════════════════════════════════════════════════════════════════════════
# 6. ESQUEMA DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
contenido += seccion("6. Esquema de Base de Datos PostgreSQL")
contenido += [
    p("La base de datos <b>ordersdb</b> tiene dos tablas relacionadas. "
      "La relación entre ellas permite rastrear exactamente qué tarea originó cada pedido:"),
    Spacer(1, 0.3*cm),
]

datos_schema = [
    [Paragraph("<b>Tabla: tasks</b>", cuerpo_bold), Paragraph("<b>Tipo</b>", cuerpo_bold),
     Paragraph("<b>Descripción</b>", cuerpo_bold)],
    [Paragraph("task_id", cuerpo), Paragraph("UUID (PK)", cuerpo),
     Paragraph("Identificador único de la tarea asíncrona", cuerpo)],
    [Paragraph("status", cuerpo), Paragraph("VARCHAR(20)", cuerpo),
     Paragraph("Estado actual: 'pendiente' → 'completado'", cuerpo)],
    [Paragraph("created_at", cuerpo), Paragraph("TIMESTAMPTZ", cuerpo),
     Paragraph("Fecha y hora de creación (con zona horaria UTC)", cuerpo)],
    [Paragraph("updated_at", cuerpo), Paragraph("TIMESTAMPTZ", cuerpo),
     Paragraph("Fecha de última actualización (lo actualiza el Worker)", cuerpo)],
]
t1 = Table(datos_schema, colWidths=[4*cm, 4*cm, 8.5*cm])
t1.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
contenido.append(t1)
contenido.append(Spacer(1, 0.4*cm))

datos_schema2 = [
    [Paragraph("<b>Tabla: orders</b>", cuerpo_bold), Paragraph("<b>Tipo</b>", cuerpo_bold),
     Paragraph("<b>Descripción</b>", cuerpo_bold)],
    [Paragraph("order_id", cuerpo), Paragraph("UUID (PK)", cuerpo),
     Paragraph("Identificador único del pedido, generado por el Worker", cuerpo)],
    [Paragraph("task_id", cuerpo), Paragraph("UUID (FK → tasks)", cuerpo),
     Paragraph("Referencia a la tarea que originó este pedido", cuerpo)],
    [Paragraph("payload", cuerpo), Paragraph("JSONB", cuerpo),
     Paragraph("Datos del pedido (description, quantity, product). "
               "JSONB permite actualizar campos individuales con el operador '||'", cuerpo)],
    [Paragraph("created_at", cuerpo), Paragraph("TIMESTAMPTZ", cuerpo),
     Paragraph("Fecha de creación del pedido", cuerpo)],
]
t2 = Table(datos_schema2, colWidths=[4*cm, 4*cm, 8.5*cm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
contenido.append(t2)

# ══════════════════════════════════════════════════════════════════════════════
# 7. ENDPOINTS DE LA API
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("7. Endpoints de la API REST")

datos_endpoints = [
    [Paragraph("<b>Método</b>", cuerpo_bold), Paragraph("<b>Ruta</b>", cuerpo_bold),
     Paragraph("<b>Tipo</b>", cuerpo_bold), Paragraph("<b>Descripción</b>", cuerpo_bold),
     Paragraph("<b>HTTP</b>", cuerpo_bold)],
    [Paragraph("GET", cuerpo), Paragraph("/health", cuerpo),
     Paragraph("Síncrono", cuerpo),
     Paragraph("Verificación de salud. HAProxy lo usa para saber si la API está activa", cuerpo),
     Paragraph("200", cuerpo)],
    [Paragraph("POST", cuerpo), Paragraph("/orders", cuerpo),
     Paragraph("Asíncrono", cuerpo),
     Paragraph("Crea un pedido. Retorna task_id. El Worker procesa en segundo plano", cuerpo),
     Paragraph("202", cuerpo)],
    [Paragraph("GET", cuerpo), Paragraph("/orders", cuerpo),
     Paragraph("Síncrono", cuerpo),
     Paragraph("Lista todos los pedidos ordenados del más reciente al más antiguo", cuerpo),
     Paragraph("200", cuerpo)],
    [Paragraph("PUT", cuerpo), Paragraph("/orders/{id}", cuerpo),
     Paragraph("Síncrono", cuerpo),
     Paragraph("Actualiza campos del pedido usando merge JSONB", cuerpo),
     Paragraph("200", cuerpo)],
    [Paragraph("DELETE", cuerpo), Paragraph("/orders/{id}", cuerpo),
     Paragraph("Asíncrono", cuerpo),
     Paragraph("Elimina un pedido. Retorna task_id. El Worker ejecuta el DELETE", cuerpo),
     Paragraph("202", cuerpo)],
    [Paragraph("GET", cuerpo), Paragraph("/tasks/{id}", cuerpo),
     Paragraph("Síncrono", cuerpo),
     Paragraph("Consulta el estado de una tarea (pendiente → completado)", cuerpo),
     Paragraph("200/404", cuerpo)],
]
t_ep = Table(datos_endpoints, colWidths=[1.8*cm, 3.5*cm, 2.5*cm, 7.2*cm, 1.5*cm])
t_ep.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
]))
contenido.append(t_ep)
contenido.append(Spacer(1, 0.4*cm))

# ══════════════════════════════════════════════════════════════════════════════
# 8. GUÍA DE DESPLIEGUE
# ══════════════════════════════════════════════════════════════════════════════
contenido += seccion("8. Guía Paso a Paso: Despliegue en AWS Learner Lab")

contenido += subseccion("Paso 1 — Obtener credenciales AWS del Learner Lab")
contenido += [
    p("En la consola del Learner Lab: <b>AWS Details → Show → Copiar las 3 variables</b>"),
    cod("export AWS_ACCESS_KEY_ID=ASIA..."),
    cod("export AWS_SECRET_ACCESS_KEY=..."),
    cod("export AWS_SESSION_TOKEN=..."),
    Spacer(1, 0.2*cm),
]

contenido += subseccion("Paso 2 — Actualizar VPC y Subnet en variables.tf")
contenido += [
    p("Las IDs de VPC y subnet cambian con cada sesión del Learner Lab. Obtenerlas con:"),
    cod("aws ec2 describe-vpcs --region us-east-1 --query 'Vpcs[*].{VpcId:VpcId}' --output table"),
    cod("aws ec2 describe-subnets --region us-east-1 --filters 'Name=vpc-id,Values=VPC_ID'"),
    p("Actualizar <i>variables.tf</i>: campos <b>vpc_id</b> y <b>subnet_id</b>."),
    Spacer(1, 0.2*cm),
]

contenido += subseccion("Paso 3 — Desplegar toda la infraestructura")
contenido += [
    cod("cd proyecto/terraform"),
    cod("terraform init        # Descarga el proveedor AWS"),
    cod("terraform apply -auto-approve   # Crea los 9 recursos en ~30 segundos"),
    Spacer(1, 0.1*cm),
    p("Al terminar, Terraform muestra las IPs de todas las instancias y la URL del Swagger."),
    Spacer(1, 0.2*cm),
]

contenido += subseccion("Paso 4 — Verificar que la API está lista (~3-5 minutos)")
contenido += [
    p("Los scripts de instalación (user_data) tardan varios minutos en ejecutarse. "
      "Esperar hasta que el health check responda:"),
    cod("curl http://HAPROXY_IP/health"),
    cod("# Respuesta esperada: {\"estado\": \"saludable\"}"),
    Spacer(1, 0.2*cm),
]

contenido += subseccion("Paso 5 — Probar todos los endpoints")
contenido += [
    cod("# Crear pedido (asíncrono — retorna 202)"),
    cod("curl -X POST http://HAPROXY_IP/orders \\"),
    cod("  -H 'Content-Type: application/json' \\"),
    cod("  -d '{\"description\": \"Mi pedido\", \"quantity\": 3, \"product\": \"Widget A\"}'"),
    Spacer(1, 0.15*cm),
    cod("# Verificar estado de la tarea"),
    cod("curl http://HAPROXY_IP/tasks/TASK_ID"),
    Spacer(1, 0.15*cm),
    cod("# Listar pedidos"),
    cod("curl http://HAPROXY_IP/orders"),
    Spacer(1, 0.15*cm),
    cod("# Destruir infraestructura (para no gastar créditos del Learner Lab)"),
    cod("terraform destroy -auto-approve"),
    Spacer(1, 0.3*cm),
]

# ══════════════════════════════════════════════════════════════════════════════
# 9. DECISIONES DE DISEÑO — POR QUÉ IAAS Y NO SERVERLESS
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("9. Decisiones de Diseño: ¿Por qué IaaS y no Serverless?")
contenido += [
    p("Durante el curso se trabajaron dos modelos de cómputo en AWS:"),
    Spacer(1, 0.1*cm),
]

datos_iaas_vs = [
    [Paragraph("<b>Característica</b>", cuerpo_bold),
     Paragraph("<b>Serverless (Lambda)</b>", cuerpo_bold),
     Paragraph("<b>IaaS (EC2) — Este Proyecto</b>", cuerpo_bold)],
    [Paragraph("Control del SO", cuerpo),
     Paragraph("Sin acceso — AWS gestiona todo", cuerpo),
     Paragraph("Control total: instalar cualquier software", cuerpo)],
    [Paragraph("Servicios de terceros", cuerpo),
     Paragraph("Limitado a servicios AWS", cuerpo),
     Paragraph("Cualquier software: RabbitMQ, HAProxy, PostgreSQL", cuerpo)],
    [Paragraph("Servidor largo corriendo", cuerpo),
     Paragraph("No aplica (stateless, efímero)", cuerpo),
     Paragraph("El Worker necesita correr indefinidamente escuchando colas", cuerpo)],
    [Paragraph("Complejidad de red", cuerpo),
     Paragraph("Lambda gestiona la red automáticamente", cuerpo),
     Paragraph("Requiere configurar VPC, security groups, subnets", cuerpo)],
    [Paragraph("Costo en lab", cuerpo),
     Paragraph("Créditos por ejecución", cuerpo),
     Paragraph("t3.micro casi gratuito en Learner Lab", cuerpo)],
    [Paragraph("Aprendizaje", cuerpo),
     Paragraph("Oculta la infraestructura subyacente", cuerpo),
     Paragraph("Expone todos los conceptos de red y sistemas operativos", cuerpo)],
]
t_iaas = Table(datos_iaas_vs, colWidths=[4*cm, 6*cm, 6.5*cm])
t_iaas.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
]))
contenido.append(t_iaas)
contenido.append(Spacer(1, 0.3*cm))
contenido += [
    p("La decisión de usar IaaS fue deliberada: el objetivo era demostrar el dominio "
      "de todos los conceptos vistos en el curso (redes, seguridad, contenedores, mensajería, "
      "bases de datos) en una solución integrada. Lambda habría ocultado esa complejidad."),
]

# ══════════════════════════════════════════════════════════════════════════════
# 10. RESUMEN DE PRUEBAS
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("10. Resumen de Pruebas")

contenido += subseccion("10.1 Pruebas Unitarias (pytest — 17 tests, 100% pasando)")
datos_tests = [
    [Paragraph("<b>Test</b>", cuerpo_bold), Paragraph("<b>Qué verifica</b>", cuerpo_bold)],
    [Paragraph("test_health", cuerpo), Paragraph("GET /health retorna {\"estado\": \"saludable\"}", cuerpo)],
    [Paragraph("test_create_order_returns_202", cuerpo), Paragraph("POST /orders retorna HTTP 202 con task_id y estado='pendiente'", cuerpo)],
    [Paragraph("test_create_order_inserts_task_and_publishes", cuerpo), Paragraph("La API inserta en BD Y publica en RabbitMQ", cuerpo)],
    [Paragraph("test_create_order_db_error_returns_500", cuerpo), Paragraph("Error de BD retorna HTTP 500", cuerpo)],
    [Paragraph("test_get_task_found", cuerpo), Paragraph("Tarea existente retorna sus datos con estado", cuerpo)],
    [Paragraph("test_get_task_not_found", cuerpo), Paragraph("UUID válido pero inexistente retorna 404", cuerpo)],
    [Paragraph("test_get_task_invalid_uuid_returns_404", cuerpo), Paragraph("UUID con formato inválido retorna 404 (no 500)", cuerpo)],
    [Paragraph("test_get_task_invalid_uuid_message", cuerpo), Paragraph("Mensaje de error correcto en español y género", cuerpo)],
    [Paragraph("test_get_task_db_error_returns_500", cuerpo), Paragraph("Error de BD en consulta retorna HTTP 500", cuerpo)],
    [Paragraph("test_get_orders_empty", cuerpo), Paragraph("Lista vacía retorna [] con HTTP 200", cuerpo)],
    [Paragraph("test_get_orders_with_data", cuerpo), Paragraph("Lista con pedidos retorna los campos en español", cuerpo)],
    [Paragraph("test_update_order_success", cuerpo), Paragraph("PUT actualiza y retorna pedido_id y estado='actualizado'", cuerpo)],
    [Paragraph("test_update_order_not_found", cuerpo), Paragraph("PUT con pedido inexistente retorna 404", cuerpo)],
    [Paragraph("test_update_order_invalid_uuid_returns_404", cuerpo), Paragraph("UUID inválido en PUT retorna 404", cuerpo)],
    [Paragraph("test_delete_order_returns_202", cuerpo), Paragraph("DELETE retorna 202 con task_id", cuerpo)],
    [Paragraph("test_delete_order_not_found", cuerpo), Paragraph("DELETE con pedido inexistente retorna 404", cuerpo)],
    [Paragraph("test_delete_order_invalid_uuid_returns_404", cuerpo), Paragraph("UUID inválido en DELETE retorna 404", cuerpo)],
]
t_tests = Table(datos_tests, colWidths=[7.5*cm, 9*cm])
t_tests.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), VERDE),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F8E9")]),
    ("GRID", (0,0), (-1,-1), 0.5, GRIS_BORDE),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("TOPPADDING", (0,0), (-1,-1), 3),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]))
contenido.append(t_tests)
contenido.append(Spacer(1, 0.3*cm))

contenido += subseccion("10.2 Pruebas de Integración en Producción (AWS)")
contenido += [
    p("Después del despliegue en AWS, se verificaron manualmente todos los flujos:"),
    Spacer(1, 0.1*cm),
    cod("✓  GET /health → {\"estado\": \"saludable\"}  (HTTP 200)"),
    cod("✓  POST /orders → task_id generado  (HTTP 202)"),
    cod("✓  Flujo asíncrono: tarea pasa a 'completado' en < 1 segundo"),
    cod("✓  GET /orders → lista el pedido creado con sus datos"),
    cod("✓  PUT /orders/{id} → actualiza quantity y description en JSONB"),
    cod("✓  DELETE /orders/{id} → tarea completada y lista vacía"),
    cod("✓  UUID inválido → HTTP 404 con mensaje en español (no HTTP 500)"),
    cod("✓  Load balancer → HAProxy distribuye entre API-1 y API-2"),
    Spacer(1, 0.3*cm),
]

contenido += subseccion("10.3 Análisis Estático de Código (ruff)")
contenido += [
    cod("ruff check api/ worker/ producer/"),
    cod("# Resultado: 0 errores (7 corregidos automáticamente con --fix)"),
    p("Los errores corregidos fueron: imports sin usar, imports desordenados. "
      "ruff es más rápido que flake8+black combinados y se configuró en pyproject.toml."),
    Spacer(1, 0.3*cm),
]

# ══════════════════════════════════════════════════════════════════════════════
# CIERRE
# ══════════════════════════════════════════════════════════════════════════════
contenido += [PageBreak()]
contenido += seccion("Conclusiones")
contenido += [
    p("Este proyecto integra de forma cohesiva todas las tecnologías estudiadas durante "
      "el semestre de Computación en la Nube. Cada componente tiene una justificación "
      "técnica clara y está conectado directamente con alguna práctica del curso."),
    Spacer(1, 0.2*cm),
    p("La arquitectura asíncrona con RabbitMQ demuestra un patrón real de la industria: "
      "desacoplar la recepción de peticiones de su procesamiento, permitiendo que el sistema "
      "escale horizontalmente añadiendo más Workers o más instancias de la API detrás del "
      "balanceador sin cambiar el código."),
    Spacer(1, 0.2*cm),
    p("El uso de Terraform garantiza que la infraestructura es reproducible: cualquier persona "
      "con acceso al repositorio y credenciales de AWS puede recrear el sistema completo "
      "en menos de 5 minutos con un solo comando."),
    Spacer(1, 0.2*cm),
    p("La cobertura de tests del 100% de los endpoints y el análisis estático con ruff "
      "aseguran que el código es correcto y mantenible, siguiendo estándares de calidad "
      "de la industria."),
    Spacer(1, 0.8*cm),
    HRFlowable(width="100%", thickness=1, color=GRIS_BORDE),
    Spacer(1, 0.3*cm),
    Paragraph("Repositorio: github.com/izqsebas-sys/proyecto-cloud", info_portada),
    Paragraph("Generado automáticamente con reportlab · Mayo 2026", info_portada),
]

# ─── Generar el PDF ───────────────────────────────────────────────────────────
doc.build(contenido)
print("PDF generado: Instructivo_Proyecto_Cloud.pdf")
