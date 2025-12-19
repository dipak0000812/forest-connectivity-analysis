import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

requirements = [
    "numpy",
    "scipy",
    "pandas",
    "geopandas",
    "rasterio",
    "shapely",
    "matplotlib",
    "folium",
    "requests",
    "dotenv"
]

print("-" * 20)
print("Checking dependencies...")
for req in requirements:
    try:
        module = __import__(req)
        print(f"[OK] {req}")
    except ImportError as e:
        print(f"[FAIL] {req}: {e}")
        if req == "dotenv":
             try:
                 import dotenv
                 print(f"[OK] dotenv (via python-dotenv)")
             except ImportError:
                 print(f"[FAIL] dotenv")

print("-" * 20)
print("Checking src modules...")
try:
    from src.connectivity import ConnectivityAnalyzer
    print("[OK] src.connectivity")
except ImportError as e:
    print(f"[FAIL] src.connectivity: {e}")

try:
    from src.vectorization import raster_to_polygons
    print("[OK] src.vectorization")
except ImportError as e:
    print(f"[FAIL] src.vectorization: {e}")
