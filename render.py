"""
Script d'initialisation pour Render.com
"""
import os
import sys
import subprocess
import time

def patch_django():
    """Patch Django to accept our domain"""
    try:
        import django.http.request
        
        request_file = django.http.request.__file__
        print(f"Django request file: {request_file}")
        
        with open(request_file, 'r') as f:
            content = f.read()
        
        # Backup
        with open(f"{request_file}.bak", 'w') as f:
            f.write(content)
        
        # Patch
        if 'martialcomp.onrender.com' not in content:
            content = content.replace(
                'raise DisallowedHost(msg)', 
                'if "martialcomp.onrender.com" in host: return host\n        raise DisallowedHost(msg)'
            )
            
            with open(request_file, 'w') as f:
                f.write(content)
            
            print("Django patched successfully!")
        else:
            print("Django already patched.")
        
        return True
    except Exception as e:
        print(f"Error patching Django: {str(e)}")
        return False

def start_application():
    """Start the application with gunicorn"""
    print("Starting application...")
    port = os.environ.get('PORT', '10000')
    cmd = ['gunicorn', 'config.wsgi:application', f'--bind=0.0.0.0:{port}']
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    # Patch Django
    patch_result = patch_django()
    print(f"Patch result: {patch_result}")
    
    # Start the application
    start_application()