import settings
import os
import json

def hex_to_decimal(hex_color):
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return r, g, b

def write_settings_to_file(device, effect="", color="", dpi=""):
    """ Save settings to a file for possible later retrieval """
    
    home_dir = os.path.expanduser("~")
    dir_name = settings.CACHE_DIR
    file_name = settings.CACHE_FILE
    path_and_file = os.path.join(home_dir, dir_name, file_name)

    # Handle non-existing file
    if not os.path.isfile(path_and_file):
        os.makedirs(os.path.dirname(path_and_file), exist_ok=True)
        print("creating path and file")
        a = []
        with open(path_and_file, mode='w') as file:
            json.dump(a, file)

    # Check if there already exists an entry for this device, if yes update it
    found_existing_settings = False
    with open(path_and_file, 'r') as file:
         json_data = json.load(file)
         for item in json_data:
             if (item['device_name'] == device.name):
                 found_existing_settings = True
                 if (color != ""):
                    item['color'] = color
                 if (effect != ""):
                    item['effect'] = effect
                 if (dpi != ""):
                    item['dpi'] = dpi

    # Update existing entry
    if found_existing_settings:
        with open(path_and_file, 'w') as file:
            json.dump(json_data, file, indent=2)
    # If no existing entry was found, append a new entry
    else:
        print("Adding new settings entry")
        used_settings = {}
        used_settings['device_name'] = device.name
        if (color != ""):
            used_settings['color'] = color
        if (effect != ""):
            used_settings['effect'] = effect
        if (dpi != ""):
            used_settings['dpi'] = dpi
        with open(path_and_file, mode='w') as file:
            json_data.append(used_settings)
            json.dump(json_data, file, indent=2)
