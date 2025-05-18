import json
from jsonschema import validate, ValidationError
import os

def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def validate_access_config():
    try:
        # Load schema and config
        schema = load_json_file('modules/access/schema.json')
        config = load_json_file('modules/access/access.json')
        
        # Validate
        validate(instance=config, schema=schema)
        print("✅ Access configuration is valid!")
        
        # Additional checks
        print("\nConfiguration Summary:")
        for user_type, user_config in config['users'].items():
            print(f"\nUser Type: {user_type}")
            print(f"Permission Level: {user_config['permission_level']}")
            print("Modules:")
            for module_name, module_config in user_config['modules'].items():
                print(f"  - {module_name}")
                print(f"    Unlocked: {module_config['unlocked']}")
                print(f"    Version: {module_config['version']}")
                print("    Features:")
                for feature, enabled in module_config['features'].items():
                    print(f"      - {feature}: {enabled}")
        
    except ValidationError as e:
        print(f"❌ Validation Error: {e.message}")
        print(f"Path: {'.'.join(str(p) for p in e.path)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    validate_access_config() 