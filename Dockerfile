FROM nginx:alpine

# Copiar archivos de la aplicación
COPY index.html /usr/share/nginx/html/
COPY app.html /usr/share/nginx/html/
COPY costos_mensuales.html /usr/share/nginx/html/
COPY operatividad_vehiculos.html /usr/share/nginx/html/
COPY img/ /usr/share/nginx/html/img/

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
