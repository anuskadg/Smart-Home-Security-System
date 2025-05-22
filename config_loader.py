import json

def load_config(config_path='config.json'):
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str): Path to the configuration file
    
    Returns:
        dict: Loaded configuration dictionary
    """
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in config file at {config_path}")
        return None