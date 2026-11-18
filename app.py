import streamlit as st
from PIL import Image
import io
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
        try:
            remitente = st.secrets["EMAIL_USER"]
            password = st.secrets["EMAIL_PASS"]
        except Exception:
            st.error("⚠️ Faltan configurar los Secrets en Streamlit Cloud (EMAIL_USER y EMAIL_PASS).")
            st.stop()

        with st.spinner("Optimizando fotos y preparando correo..."):
            try:
                msg = EmailMessage()
                msg['Subject'] = f"[Reporte Tottus] Tienda: {nombre_tienda} | Mercaderista: {nombre_mercaderista} - {fecha_hoy}"
                msg['From'] = remitente
                
                destinatarios = [email_destino]
                if email_copia:
                    destinatarios.append(email_copia)
                msg['To'] = ", ".join(destinatarios)
                
                cuerpo_mensaje = f"""Hola,\n\nSe ha enviado un nuevo reporte fotográfico:\n- Mercaderista: {nombre_mercaderista}\n- Tienda: {nombre_tienda}\n- Fecha: {fecha_hoy}\n\nObservaciones:\n{comentarios if comentarios else 'Ninguna.'}\n\nLas fotos se encuentran adjuntas individualmente en este correo.\n\nReporte generado automáticamente desde la App de Rutas."""
                msg.set_content(cuerpo_mensaje)

                # Función para procesar y adjuntar cada foto individualmente
                def adjuntar_fotos(lista_archivos, nombre_categoria):
                    if lista_archivos:
                        for i, archivo in enumerate(lista_archivos):
                            img = Image.open(archivo)
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.thumbnail((1280, 1280))
                            
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=85)
                            
                            nombre_archivo = f"{nombre_categoria}_{i+1}.jpg"
                            msg.add_attachment(
                                img_byte_arr.getvalue(),
                                maintype='image',
                                subtype='jpeg',
                                filename=nombre_archivo
                            )

                # Añadir fotos de cada sección como archivos independientes
                adjuntar_fotos(fotos_ferreteria, "Ferreteria")
                adjuntar_fotos(fotos_iluminacion, "Iluminacion")
                adjuntar_fotos(fotos_automotor, "Automotor")
                adjuntar_fotos(fotos_adicional, "Exhibicion_Adicional")

                # Conexión SMTP
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(remitente, password)
                    smtp.send_message(msg)

                st.success("¡Reporte y fotos enviados con éxito! 🎉")
                
            except Exception as e:
                st.error(f"Error al enviar: {e}")
