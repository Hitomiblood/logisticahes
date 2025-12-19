"""
Script para descargar archivos de SharePoint usando Playwright (sesión OTP)
y prepararlos para Docker deployment.
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    os.system("pip install playwright")
    from playwright.async_api import async_playwright


# Configuración
SHAREPOINT_LINK = "https://hesegoingsas.sharepoint.com/:f:/s/Logstica/IgBVeTGKoK1vSLo4HvK44o_cAV_fvC2qeAbqQbGlisRCNTs?e=5%3aJBYZkS&at=9"
EMAIL = "gerencia@rastrear.com.co"
BASE_DIR = Path(__file__).parent
DOWNLOAD_FOLDER = BASE_DIR / "data"
DOCKER_DATA_FOLDER = BASE_DIR / "docker_data"  # Para copiar al servidor


# Carpetas a sincronizar
FOLDERS_TO_SYNC = [
    "TRANSPORTE",
    "ALMACENES", 
    "COMPRAS"
]


async def download_sharepoint_files():
    """Descarga archivos de SharePoint navegando por las carpetas."""
    
    # Crear carpetas
    DOWNLOAD_FOLDER.mkdir(exist_ok=True)
    DOCKER_DATA_FOLDER.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(DOWNLOAD_FOLDER)
        )
        
        context = await browser.new_context(
            accept_downloads=True
        )
        
        # Configurar descargas automáticas
        page = await context.new_page()
        
        print("=" * 60)
        print("📥 DESCARGADOR DE ARCHIVOS SHAREPOINT")
        print("=" * 60)
        print(f"📁 Carpeta de descargas: {DOWNLOAD_FOLDER}")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        # Navegar a SharePoint
        await page.goto(SHAREPOINT_LINK, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Ingresar correo si es necesario
        try:
            email_input = page.locator('input[type="email"], input[placeholder*="correo"]')
            if await email_input.count() > 0:
                await email_input.first.fill(EMAIL)
                print(f"✓ Correo ingresado: {EMAIL}")
                
                next_button = page.locator('input[type="submit"], button:has-text("Siguiente")')
                if await next_button.count() > 0:
                    await next_button.first.click()
                    await asyncio.sleep(3)
        except Exception:
            pass
        
        # Esperar OTP si es necesario
        if "guestaccess" in page.url.lower():
            print("\n📧 Ingresa el código OTP en el navegador...")
            print("   Esperando acceso a la carpeta...\n")
            
            # Esperar hasta acceder
            while "guestaccess" in page.url.lower():
                await asyncio.sleep(2)
        
        print("✓ Acceso a SharePoint confirmado")
        await asyncio.sleep(3)
        
        # Función para descargar archivos de una carpeta
        async def download_folder_contents(folder_name: str):
            print(f"\n📂 Procesando carpeta: {folder_name}")
            print("-" * 40)
            
            # Buscar y hacer clic en la carpeta
            folder_link = page.locator(f'button:has-text("{folder_name}"), a:has-text("{folder_name}")')
            
            if await folder_link.count() > 0:
                await folder_link.first.click()
                await asyncio.sleep(3)
                
                # Obtener lista de archivos
                files = await page.locator('[data-automationid="FieldRenderer-name"]').all()
                
                downloaded = 0
                for file_elem in files:
                    file_name = await file_elem.text_content()
                    if file_name and '.' in file_name:  # Es un archivo, no carpeta
                        print(f"  📄 {file_name}")
                        
                        # Hacer clic derecho y descargar
                        await file_elem.click(button='right')
                        await asyncio.sleep(1)
                        
                        download_option = page.locator('button:has-text("Descargar"), span:has-text("Descargar")')
                        if await download_option.count() > 0:
                            async with page.expect_download() as download_info:
                                await download_option.first.click()
                            download = await download_info.value
                            
                            # Guardar archivo
                            save_path = DOWNLOAD_FOLDER / folder_name / download.suggested_filename
                            save_path.parent.mkdir(exist_ok=True)
                            await download.save_as(str(save_path))
                            print(f"     ✓ Descargado: {save_path.name}")
                            downloaded += 1
                        
                        await asyncio.sleep(1)
                
                print(f"  Total descargados: {downloaded} archivos")
                
                # Volver atrás
                await page.go_back()
                await asyncio.sleep(2)
            else:
                print(f"  ⚠ Carpeta no encontrada")
        
        # Procesar cada carpeta
        for folder in FOLDERS_TO_SYNC:
            try:
                await download_folder_contents(folder)
            except Exception as e:
                print(f"  ✗ Error en {folder}: {e}")
        
        print("\n" + "=" * 60)
        print("✓ DESCARGA COMPLETADA")
        print("=" * 60)
        print(f"\n📁 Archivos guardados en: {DOWNLOAD_FOLDER}")
        
        # Mostrar instrucciones para Docker
        print("\n" + "=" * 60)
        print("🐳 PARA DESPLEGAR EN DOCKER:")
        print("=" * 60)
        print("""
1. Copia la carpeta 'data' al servidor:
   scp -r ./data usuario@servidor:/ruta/proyecto/

2. O sube a un repositorio y clona en el servidor

3. En el servidor, ejecuta:
   docker-compose up -d --build
        """)
        
        input("\nPresiona ENTER para cerrar el navegador...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(download_sharepoint_files())
