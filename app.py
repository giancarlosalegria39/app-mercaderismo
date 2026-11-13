import streamlit as st
from PIL import Image
import io
import zipfile
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Configuración de la página para dispositivos móviles
st.set_page_config(
    page_title="Reporte Tottus - Mercaderista",
    page_icon="🛒",
    layout="centered"
)

st.title("🛒 Reporte Tottus: Electro & Ferretería")
st.write("Selecciona tu tienda, sube las fotos por sección y envíalas directo al correo.")

# --- 1. DATOS DE LA VISITA Y RUTA ---
st.subheader("1. Datos de la Tienda")

rutas_frecuentes = [
    "Tottus Huaylas",
    "Tottus Pachacútec",
    "Tottus Villa El Salvador",
    "Tai Loy Angamos",
    "Otra tienda (Personalizada)"
]

seleccion_ruta = st.selectbox("Selecciona tu Tienda / Ruta:", rutas_frecuentes)

if seleccion_ruta == "Otra tienda (Personalizada)":
    nombre_tienda = st.text_input("Escribe el nombre de la tienda:")
else:
    nombre_tienda = seleccion_ruta

# Selector de Área principal en Tottus
area_tottus = st.selectbox("Área de Trabajo:", ["Electro", "Ferretería / Hogar", "Ambas áreas"])

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
st.text(f"📅 Fecha: {fecha_hoy}")

comentarios = st.text_area("Observaciones (Quiebres, precios erróneos, exhibiciones):", placeholder="Ej. Falta exhibir tal modelo en Electro...")

# --- 2. REGISTRO FOTOGRÁFICO POR ZONA ---
st.subheader("2. Registro de Fotos")
st.write("Sube las fotos correspondientes a cada zona:")

tab1, tab2, tab3, tab4 = st.tabs(["Lineal / Góndola", "Cabeceras (Puntas)", "Precios / Viñetas", "Exhibición Adicional"])

with tab1:
    st.markdown("### 🏬 Lineal Principal (Góndola)")
    fotos_gondola = st.file_uploader("Fotos de Lineal", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="gondola")

with tab2:
    st.markdown("### 🎯 Cabeceras / Puntas de Góndola")
    fotos_cabecera = st.file_uploader("Fotos de Cabeceras", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cabecera")

with tab3:
    st.markdown("### 💲 Precios y Viñetas / Cenefas")
    fotos_precios = st.file_uploader("Fotos de Precios", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="precios")

with tab4:
    st.markdown("### 📦 Exhibición Adicional / Isla")
    fotos_adicional = st.file_uploader("Fotos Adicionales", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="adicional")

# --- 3. PROCESAMIENTO Y ENVÍO ---
st.markdown("---")
email_destino = st.text_input("Correo del Supervisor:", placeholder="supervisor@empresa.com")

if st.button("🚀 Procesar y Enviar Reporte", type="primary"):
    if not nombre_tienda:
        st.error("Por favor selecciona o ingresa una tienda.")
    elif not email_destino:
        st.error("Por favor ingresa el correo del destinatario.")
    else:
        with st.spinner("Optimizando fotos y creando reporte comprimido..."):
            try:
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    
                    def agregar_fotos_a_zip(lista_archivos, nombre_carpeta):
                        for i, archivo in enumerate(lista_archivos):
                            img = Image.open(archivo)
                            
                            # Evita error si la imagen tiene transparencia (RGBA / P)
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                                
                            img.thumbnail((1280, 1280))
                            
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=85)
                            img_byte_arr = img_byte_arr.getvalue()
                            
                            nombre_archivo = f"{nombre_carpeta}_{i+1}.jpg"
                            ruta_en_zip = f"{nombre_tienda.replace(' ', '_')}_{area_tottus}_{fecha_hoy}/{nombre_carpeta}/{nombre_archivo}"
                            
                            zip_file.writestr(ruta_en_zip, img_byte_arr)

                    if fotos_gondola:
                        agregar_fotos_a_zip(fotos_gondola, "01_Lineal_Gondola")
                    if fotos_cabecera:
                        agregar_fotos_a_zip(fotos_cabecera, "02_Cabeceras")
                    if fotos_precios:
                        agregar_fotos_a_zip(fotos_precios, "03_Precios_Viñetas")
                    if fotos_adicional:
                        agregar_fotos_a_zip(fotos_adicional, "04_Exhibicion_Adicional")
                    
                    if comentarios:
                        zip_file.writestr(f"{nombre_tienda.replace(' ', '_')}_{area_tottus}_{fecha_hoy}/observaciones.txt", comentarios)

                zip_buffer.seek(0)

                # Configuración de Envío SMTP usando puerto 587 y STARTTLS
                remitente = st.secrets["EMAIL_USER"]
                password = st.secrets["EMAIL_PASS"]

                msg = EmailMessage()
                msg['Subject'] = f"[Reporte Tottus {area_tottus}] {nombre_tienda} - {fecha_hoy}"
                msg['From'] = remitente
                msg['To'] = email_destino
                
                cuerpo_mensaje = f"""Hola,\n\nAdjunto el reporte fotográfico de la visita:\n- Tienda: {nombre_tienda}\n- Área: {area_tottus}\n- Fecha: {fecha_hoy}\n\nObservaciones:\n{comentarios if comentarios else 'Ninguna.'}\n\nReporte generado automáticamente desde la App de Rutas."""
                msg.set_content(cuerpo_mensaje)

                nombre_zip = f"Reporte_{nombre_tienda.replace(' ', '_')}_{area_tottus}_{fecha_hoy}.zip"
                msg.add_attachment(zip_buffer.getvalue(), maintype='application', subtype='zip', filename=nombre_zip)

                # Conexión segura mediante puerto 587 con STARTTLS
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(remitente, password)
                    smtp.send_message(msg)

                st.success("¡Reporte enviado con éxito al supervisor! 🎉")
                
            except Exception as e:
                st.error(f"Error al enviar: {e}")
