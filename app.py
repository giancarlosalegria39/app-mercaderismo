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

st.title("🛒 Reporte Tottus: Ferretería & Secciones")
st.write("Registra tus datos, sube las fotos por sección y envía tu reporte.")

# --- 1. DATOS DEL MERCADERISTA Y TIENDA ---
st.subheader("1. Datos de la Visita")

# Nuevo campo para identificar al mercaderista
nombre_mercaderista = st.text_input("👤 Tu Nombre y Apellido:", placeholder="Ej. Juan Pérez")

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

fecha_hoy = datetime.now().strftime("%Y-%m-%d")
st.text(f"📅 Fecha: {fecha_hoy}")

comentarios = st.text_area("Observaciones (Quiebres, precios erróneos, exhibiciones):", placeholder="Ej. Falta exhibir tal modelo...")

# --- 2. REGISTRO FOTOGRÁFICO POR ZONA ---
st.subheader("2. Registro de Fotos")
st.write("Sube las fotos correspondientes a cada zona:")

tab1, tab2, tab3, tab4 = st.tabs(["Ferretería", "Iluminación", "Automotor", "Exhibición Adicional"])

with tab1:
    st.markdown("### 🔧 Ferretería")
    fotos_ferreteria = st.file_uploader("Fotos de Ferretería", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="ferreteria")

with tab2:
    st.markdown("### 💡 Iluminación")
    fotos_iluminacion = st.file_uploader("Fotos de Iluminación", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="iluminacion")

with tab3:
    st.markdown("### 🚗 Automotor")
    fotos_automotor = st.file_uploader("Fotos de Automotor", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="automotor")

with tab4:
    st.markdown("### 📦 Exhibición Adicional")
    fotos_adicional = st.file_uploader("Fotos Adicionales", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="adicional")

# --- 3. CORREOS Y ENVÍO ---
st.markdown("---")
st.subheader("3. Destinatarios")
email_destino = st.text_input("Correo del Supervisor:", placeholder="supervisor@empresa.com")
email_copia = st.text_input("Tu Correo (para recibir copia de constancia):", placeholder="tucorreo@gmail.com")

if st.button("🚀 Procesar y Enviar Reporte", type="primary"):
    if not nombre_mercaderista:
        st.error("Por favor ingresa tu nombre y apellido.")
    elif not nombre_tienda:
        st.error("Por favor selecciona o ingresa una tienda.")
    elif not email_destino:
        st.error("Por favor ingresa el correo del supervisor.")
    else:
        # Verificación previa de Secrets
        try:
            remitente = st.secrets["EMAIL_USER"]
            password = st.secrets["EMAIL_PASS"]
        except Exception:
            st.error("⚠️ Faltan configurar los Secrets en Streamlit Cloud (EMAIL_USER y EMAIL_PASS).")
            st.stop()

        with st.spinner("Optimizando fotos y creando reporte comprimido..."):
            try:
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    
                    def agregar_fotos_a_zip(lista_archivos, nombre_carpeta):
                        for i, archivo in enumerate(lista_archivos):
                            img = Image.open(archivo)
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.thumbnail((1280, 1280))
                            
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=85)
                            img_byte_arr = img_byte_arr.getvalue()
                            
                            nombre_archivo = f"{nombre_carpeta}_{i+1}.jpg"
                            ruta_en_zip = f"{nombre_tienda.replace(' ', '_')}_{nombre_mercaderista.replace(' ', '_')}_{fecha_hoy}/{nombre_carpeta}/{nombre_archivo}"
                            
                            zip_file.writestr(ruta_en_zip, img_byte_arr)

                    if fotos_ferreteria:
                        agregar_fotos_a_zip(fotos_ferreteria, "01_Ferreteria")
                    if fotos_iluminacion:
                        agregar_fotos_a_zip(fotos_iluminacion, "02_Iluminacion")
                    if fotos_automotor:
                        agregar_fotos_a_zip(fotos_automotor, "03_Automotor")
                    if fotos_adicional:
                        agregar_fotos_a_zip(fotos_adicional, "04_Exhibicion_Adicional")
                    
                    if comentarios:
                        zip_file.writestr(f"{nombre_tienda.replace(' ', '_')}_{nombre_mercaderista.replace(' ', '_')}_{fecha_hoy}/observaciones.txt", comentarios)

                zip_buffer.seek(0)

                msg = EmailMessage()
                msg['Subject'] = f"[Reporte Tottus] Tienda: {nombre_tienda} | Mercaderista: {nombre_mercaderista} - {fecha_hoy}"
                msg['From'] = remitente
                
                # Configurar destinatarios principal y copia (si el usuario ingresó su correo)
                destinatarios = [email_destino]
                if email_copia:
                    destinatarios.append(email_copia)
                msg['To'] = ", ".join(destinatarios)
                
                cuerpo_mensaje = f"""Hola,\n\nSe ha enviado un nuevo reporte fotográfico:\n- Mercaderista: {nombre_mercaderista}\n- Tienda: {nombre_tienda}\n- Fecha: {fecha_hoy}\n\nObservaciones:\n{comentarios if comentarios else 'Ninguna.'}\n\nReporte generado automáticamente desde la App de Rutas."""
                msg.set_content(cuerpo_mensaje)

                nombre_zip = f"Reporte_{nombre_tienda.replace(' ', '_')}_{nombre_mercaderista.replace(' ', '_')}_{fecha_hoy}.zip"
                msg.add_attachment(zip_buffer.getvalue(), maintype='application', subtype='zip', filename=nombre_zip)

                # Conexión SMTP
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(remitente, password)
                    smtp.send_message(msg)

                st.success("¡Reporte enviado con éxito al supervisor (y copia a tu correo)! 🎉")
                
            except Exception as e:
                st.error(f"Error al enviar: {e}")
