"""
Script para acceder a SharePoint mediante enlace de invitado con código OTP.
Usa Playwright para automatizar el navegador.
"""

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    import os
    print("Instalando Playwright...")
    os.system("pip install playwright")
    os.system("playwright install chromium")
    from playwright.async_api import async_playwright


# Configuración
SHAREPOINT_LINK = "https://hesegoingsas.sharepoint.com/:f:/s/Logstica/IgBVeTGKoK1vSLo4HvK44o_cAV_fvC2qeAbqQbGlisRCNTs?e=5%3aJBYZkS&at=9"
EMAIL = "gerencia@rastrear.com.co"
DOWNLOAD_FOLDER = Path(__file__).parent / "BI_LA_Descargas"


async def login_sharepoint_otp():
    """Automatiza el login con OTP en SharePoint."""
    
    # Crear carpeta de descargas
    DOWNLOAD_FOLDER.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        # Lanzar navegador visible (headless=False)
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        # Crear contexto con persistencia para mantener sesión
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        print("=" * 50)
        print("🌐 Abriendo SharePoint...")
        print("=" * 50)
        
        # Navegar al enlace de SharePoint
        await page.goto(SHAREPOINT_LINK, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Buscar campo de correo e ingresar email
        try:
            email_input = page.locator('input[type="email"], input[name="loginfmt"], input[placeholder*="correo"]')
            if await email_input.count() > 0:
                await email_input.first.fill(EMAIL)
                print(f"✓ Correo ingresado: {EMAIL}")
                
                # Buscar y hacer clic en botón Siguiente
                next_button = page.locator('input[type="submit"], button:has-text("Siguiente"), button:has-text("Next")')
                if await next_button.count() > 0:
                    await next_button.first.click()
                    print("✓ Clic en 'Siguiente'")
                    await asyncio.sleep(3)
        except Exception as e:
            print(f"Nota: {e}")
        
        print("\n" + "=" * 50)
        print("📧 ACCIÓN REQUERIDA:")
        print("=" * 50)
        print(f"1. Revisa el correo de {EMAIL}")
        print("2. Copia el código OTP que recibiste")
        print("3. Pégalo en el navegador")
        print("4. Marca 'Mantener mi sesión iniciada'")
        print("5. Haz clic en 'Comprobar'")
        print("=" * 50)
        
        # Esperar a que el usuario complete el OTP y acceda
        print("\n⏳ Esperando a que ingreses el código...")
        print("   (El script detectará cuando accedas a la carpeta)\n")
        
        # Esperar hasta que la URL cambie (indica acceso exitoso)
        while True:
            await asyncio.sleep(2)
            current_url = page.url
            
            # Verificar si ya accedió a la carpeta
            if "guestaccess" not in current_url.lower() and "login" not in current_url.lower():
                if "sharepoint.com" in current_url:
                    print("\n✓ ¡Acceso exitoso a SharePoint!")
                    break
            
            # También verificar si hay contenido de carpeta visible
            folder_content = page.locator('[data-automationid="FieldRenderer-name"]')
            if await folder_content.count() > 0:
                print("\n✓ ¡Carpeta BI L&A accesible!")
                break
        
        await asyncio.sleep(2)
        
        # Listar archivos visibles
        print("\n📁 Contenido de la carpeta:")
        print("-" * 40)
        
        files = await page.locator('[data-automationid="FieldRenderer-name"]').all()
        file_list = []
        for file in files:
            name = await file.text_content()
            if name:
                file_list.append(name.strip())
                print(f"  📄 {name.strip()}")
        
        print("-" * 40)
        print(f"Total: {len(file_list)} elementos")
        
        # Mantener navegador abierto
        print("\n" + "=" * 50)
        print("✓ SESIÓN ACTIVA")
        print("=" * 50)
        print("El navegador permanecerá abierto.")
        print("Puedes descargar archivos manualmente.")
        print("\nPresiona ENTER en esta terminal para cerrar...")
        
        # Esperar input del usuario
        await asyncio.to_thread(input)
        
        await browser.close()
        print("Navegador cerrado.")


if __name__ == "__main__":
    asyncio.run(login_sharepoint_otp())
