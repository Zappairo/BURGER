"""
Parsers KML pour postes, GMR et GDP
"""
import os
from src.config import get_kml_path, get_cache_path
import pickle
import xml.etree.ElementTree as ET
import pandas as pd

def parse_postes_kml_optimized():
    try:
        cache_file = get_cache_path("postes_cache.pkl")
        kml_file = get_kml_path("Poste.kml")
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        tree = ET.parse(kml_file)
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        postes_data = []
        placemarks = root.findall('.//kml:Placemark', ns)
        for placemark in placemarks:
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                poste_info = {}
                essential_fields = ['Nom_du_pos', 'Identifian', 'Tension_d', 'Tension_00']
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name in essential_fields and value:
                        poste_info[name] = value
                coordinates = placemark.find('.//kml:coordinates', ns)
                if coordinates is not None and coordinates.text:
                    coords = coordinates.text.strip().split(',')
                    if len(coords) >= 2:
                        try:
                            poste_info['longitude'] = float(coords[0])
                            poste_info['latitude'] = float(coords[1])
                        except ValueError:
                            continue
                if 'longitude' in poste_info and 'latitude' in poste_info and 'Nom_du_pos' in poste_info:
                    postes_data.append(poste_info)
        df = pd.DataFrame(postes_data)
        if 'Nom_du_pos' in df.columns:
            df['Nom poste'] = df['Nom_du_pos']
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        return df
    except Exception as e:
        print(f"Erreur lors du parsing du fichier Poste.kml : {e}")
        return pd.DataFrame()

def parse_gmr_kml_optimized(high_precision=False):
    try:
        cache_suffix = "_hq" if high_precision else ""
        cache_file = get_cache_path(f"gmr_cache{cache_suffix}.pkl")
        kml_file = get_kml_path("GMR.kml")
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        tree = ET.parse(kml_file)
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        gmr_data = []
        for placemark in root.findall('.//kml:Placemark', ns):
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gmr_info = {}
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gmr_info[name] = value
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is not None and geometry.text:
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    coords_list = coords_text.split()
                    if high_precision:
                        step = 1
                    else:
                        if len(coords_list) <= 100:
                            step = 1
                        elif len(coords_list) <= 500:
                            step = max(1, len(coords_list) // 200)
                        elif len(coords_list) <= 2000:
                            step = max(1, len(coords_list) // 300)
                        else:
                            step = max(1, len(coords_list) // 400)
                    for i in range(0, len(coords_list), step):
                        coord = coords_list[i]
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                try:
                                    coord_pairs.append([float(parts[1]), float(parts[0])])
                                except ValueError:
                                    continue
                    if coord_pairs:
                        gmr_info['coordinates'] = coord_pairs
                if gmr_info and 'Siège_du_' in gmr_info:
                    gmr_data.append(gmr_info)
        df = pd.DataFrame(gmr_data)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        return df
    except Exception as e:
        print(f"Erreur lors du parsing du fichier GMR.kml : {e}")
        return pd.DataFrame()

def parse_gdp_kml_optimized(high_precision=False):
    try:
        cache_suffix = "_hq" if high_precision else ""
        cache_file = get_cache_path(f"gdp_cache{cache_suffix}.pkl")
        kml_file = get_kml_path("GDP.kml")
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        tree = ET.parse(kml_file)
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        gdp_data = []
        for placemark in root.findall('.//kml:Placemark', ns):
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gdp_info = {}
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gdp_info[name] = value
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is None:
                    geometry = placemark.find('.//kml:MultiGeometry/kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is not None and geometry.text:
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    coords_list = coords_text.split()
                    if high_precision:
                        step = 1
                    else:
                        if len(coords_list) <= 100:
                            step = 1
                        elif len(coords_list) <= 500:
                            step = max(1, len(coords_list) // 200)
                        elif len(coords_list) <= 2000:
                            step = max(1, len(coords_list) // 300)
                        else:
                            step = max(1, len(coords_list) // 400)
                    for i in range(0, len(coords_list), step):
                        coord = coords_list[i]
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                try:
                                    coord_pairs.append([float(parts[1]), float(parts[0])])
                                except ValueError:
                                    continue
                    if coord_pairs:
                        gdp_info['coordinates'] = coord_pairs
                if gdp_info and 'Poste' in gdp_info:
                    gdp_data.append(gdp_info)
        df = pd.DataFrame(gdp_data)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        return df
    except Exception as e:
        print(f"Erreur lors du parsing du fichier GDP.kml : {e}")
        return pd.DataFrame()

def parse_postes_kml():
    try:
        tree = ET.parse(get_kml_path("Poste.kml"))
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        postes_data = []
        for placemark in root.findall('.//kml:Placemark', ns):
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                poste_info = {}
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        poste_info[name] = value
                coordinates = placemark.find('.//kml:coordinates', ns)
                if coordinates is not None and coordinates.text:
                    coords = coordinates.text.strip().split(',')
                    if len(coords) >= 2:
                        poste_info['longitude'] = float(coords[0])
                        poste_info['latitude'] = float(coords[1])
                        poste_info['Geo Point'] = f"{coords[1]},{coords[0]}"
                if poste_info:
                    postes_data.append(poste_info)
        df = pd.DataFrame(postes_data)
        if 'Nom_du_pos' in df.columns:
            df['Nom poste'] = df['Nom_du_pos']
        return df
    except Exception as e:
        print(f"Erreur lors du parsing du fichier Poste.kml : {e}")
        return pd.DataFrame()

def parse_gmr_kml():
    try:
        tree = ET.parse(get_kml_path("GMR.kml"))
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        gmr_data = []
        for placemark in root.findall('.//kml:Placemark', ns):
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gmr_info = {}
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gmr_info[name] = value
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is not None and geometry.text:
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    for coord in coords_text.split():
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                coord_pairs.append([float(parts[1]), float(parts[0])])
                    if coord_pairs:
                        gmr_info['coordinates'] = coord_pairs
                if gmr_info:
                    gmr_data.append(gmr_info)
        return pd.DataFrame(gmr_data)
    except Exception as e:
        print(f"Erreur lors du parsing du fichier GMR.kml : {e}")
        return pd.DataFrame()
