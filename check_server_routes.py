#!/usr/bin/env python3
"""
Check if storage routes are properly registered in the FastAPI app.
Run this script to verify routes are loaded correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("Checking route imports...")
    from gml.api.routes.storage import router as storage_router
    print(f"✅ Storage router imported successfully")
    print(f"   Router prefix: {storage_router.prefix}")
    print(f"   Routes in router: {len(storage_router.routes)}")
    
    for route in storage_router.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', set())
            print(f"   - {list(methods)} {route.path}")
    
    print("\nChecking route registration in main app...")
    from gml.api.main import app
    
    # Find storage routes in the app
    storage_routes = []
    for route in app.routes:
        route_path = getattr(route, 'path', None)
        if route_path and 'storage' in route_path:
            methods = getattr(route, 'methods', set())
            storage_routes.append((route_path, list(methods)))
    
    if storage_routes:
        print(f"✅ Found {len(storage_routes)} storage routes in app:")
        for path, methods in storage_routes:
            print(f"   - {methods} {path}")
    else:
        print("❌ No storage routes found in app!")
        print("\nAll registered routes:")
        for route in app.routes:
            path = getattr(route, 'path', None)
            if path:
                methods = getattr(route, 'methods', set())
                print(f"   - {list(methods)} {path}")
    
    # Check if the specific upload route exists
    upload_route = None
    for route in app.routes:
        path = getattr(route, 'path', None)
        if path and path.endswith('/storage/upload'):
            upload_route = route
            break
    
    if upload_route:
        methods = getattr(upload_route, 'methods', set())
        print(f"\n✅ Upload route found: {methods} {upload_route.path}")
    else:
        print("\n❌ Upload route NOT found in app!")
        print("   Expected: POST /api/v1/storage/upload")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Route check complete!")

