"""
Script para conectarse a SharePoint y sincronizar archivos de la carpeta BI L&A
Requiere configuración de Azure AD App Registration para funcionar correctamente.
"""

import os
import sys
from pathlib import Path

# Instalar dependencias si no están instaladas
try:
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.user_credential import UserCredential
    from office365.runtime.auth.authentication_context import AuthenticationContext
except ImportError:
    print("Instalando dependencias...")
    os.system("pip install Office365-REST-Python-Client")
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.user_credential import UserCredential


class SharePointConnector:
    def __init__(self, site_url: str, username: str, password: str):
        """
        Inicializa la conexión a SharePoint.
        
        Args:
            site_url: URL del sitio de SharePoint (ej: https://hesegoingsas.sharepoint.com/sites/Logstica)
            username: Correo electrónico del usuario
            password: Contraseña del usuario
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self.ctx = None
    
    def connect(self) -> bool:
        """Establece conexión con SharePoint."""
        try:
            user_credentials = UserCredential(self.username, self.password)
            self.ctx = ClientContext(self.site_url).with_credentials(user_credentials)
            
            # Verificar conexión obteniendo información del sitio
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            print(f"✓ Conectado exitosamente a: {web.properties['Title']}")
            return True
            
        except Exception as e:
            print(f"✗ Error de conexión: {str(e)}")
            return False
    
    def list_folder_contents(self, folder_path: str) -> list:
        """
        Lista el contenido de una carpeta en SharePoint.
        
        Args:
            folder_path: Ruta relativa de la carpeta (ej: "Shared Documents/BI L&A")
        """
        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
            files = folder.files
            folders = folder.folders
            
            self.ctx.load(files)
            self.ctx.load(folders)
            self.ctx.execute_query()
            
            contents = []
            
            print(f"\n📁 Contenido de: {folder_path}")
            print("-" * 50)
            
            # Listar subcarpetas
            for subfolder in folders:
                print(f"  📂 {subfolder.properties['Name']}/")
                contents.append({
                    'name': subfolder.properties['Name'],
                    'type': 'folder'
                })
            
            # Listar archivos
            for file in files:
                size_kb = file.properties.get('Length', 0) / 1024
                print(f"  📄 {file.properties['Name']} ({size_kb:.1f} KB)")
                contents.append({
                    'name': file.properties['Name'],
                    'type': 'file',
                    'size': file.properties.get('Length', 0)
                })
            
            return contents
            
        except Exception as e:
            print(f"✗ Error al listar carpeta: {str(e)}")
            return []
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Descarga un archivo de SharePoint.
        
        Args:
            remote_path: Ruta del archivo en SharePoint
            local_path: Ruta local donde guardar el archivo
        """
        try:
            # Crear directorio local si no existe
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, "wb") as local_file:
                file = self.ctx.web.get_file_by_server_relative_url(remote_path)
                file.download(local_file)
                self.ctx.execute_query()
            
            print(f"✓ Descargado: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"✗ Error al descargar: {str(e)}")
            return False
    
    def download_folder(self, remote_folder: str, local_folder: str) -> int:
        """
        Descarga todos los archivos de una carpeta.
        
        Args:
            remote_folder: Ruta de la carpeta en SharePoint
            local_folder: Ruta local donde guardar los archivos
        """
        downloaded = 0
        
        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(remote_folder)
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()
            
            for file in files:
                file_name = file.properties['Name']
                remote_path = f"{remote_folder}/{file_name}"
                local_path = os.path.join(local_folder, file_name)
                
                if self.download_file(remote_path, local_path):
                    downloaded += 1
            
            print(f"\n✓ Total descargados: {downloaded} archivos")
            return downloaded
            
        except Exception as e:
            print(f"✗ Error al descargar carpeta: {str(e)}")
            return downloaded


def main():
    """Función principal para ejecutar el conector."""
    
    # ⚠️ CONFIGURACIÓN - Modifica estos valores
    # Para mayor seguridad, usa variables de entorno en lugar de valores hardcodeados
    
    SITE_URL = os.getenv("SP_SITE_URL", "https://hesegoingsas.sharepoint.com/sites/Logstica")
    USERNAME = os.getenv("SP_USERNAME", "")  # Tu correo
    PASSWORD = os.getenv("SP_PASSWORD", "")  # Tu contraseña
    
    # Carpeta a sincronizar
    SHAREPOINT_FOLDER = "/sites/Logstica/Shared Documents/BI L&A"
    LOCAL_FOLDER = os.path.join(os.path.dirname(__file__), "BI_LA_Sync")
    
    # Solicitar credenciales si no están configuradas
    if not USERNAME:
        USERNAME = input("Ingresa tu correo de SharePoint: ")
    if not PASSWORD:
        import getpass
        PASSWORD = getpass.getpass("Ingresa tu contraseña: ")
    
    # Conectar y sincronizar
    connector = SharePointConnector(SITE_URL, USERNAME, PASSWORD)
    
    if connector.connect():
        # Listar contenido
        contents = connector.list_folder_contents(SHAREPOINT_FOLDER)
        
        if contents:
            # Preguntar si desea descargar
            response = input("\n¿Deseas descargar todos los archivos? (s/n): ")
            if response.lower() == 's':
                connector.download_folder(SHAREPOINT_FOLDER, LOCAL_FOLDER)
                print(f"\n📂 Archivos guardados en: {LOCAL_FOLDER}")


if __name__ == "__main__":
    main()
