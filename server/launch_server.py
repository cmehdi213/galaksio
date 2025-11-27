#!/usr/bin/env python3
"""
Galaksio Server Launcher
Updated for compatibility with GalaksioServer class and modern configuration.
"""

import os
import shutil
import sys
import configparser

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the server class
# Try importing from server module (server.py)
try:
    from server import GalaksioServer
except ImportError:
    # If running as a script, we might need to adjust path or import differently
    try:
        from .server import GalaksioServer
    except ImportError:
        # Fallback if both fail (e.g. if 'server' package name conflict)
        import server
        GalaksioServer = server.GalaksioServer

def setup_configuration():
    """Setup configuration files and environment variables."""
    is_first_launch = False

    base_dir = os.path.dirname(os.path.realpath(__file__))
    conf_dir = os.path.join(base_dir, "conf")
    res_dir = os.path.join(base_dir, "resources")
    config_file = os.path.join(conf_dir, "server.cfg")

    # Ensure conf directory exists
    os.makedirs(conf_dir, exist_ok=True)

    # Check if config file exists
    if not os.path.isfile(config_file):
        print("Configuration not found, creating new settings file from example")
        try:
            # Copy example configuration files
            shutil.copyfile(os.path.join(res_dir, "example_serverconf.cfg"), config_file)

            # Copy logging config if it exists
            if os.path.isfile(os.path.join(res_dir, "logging.cfg")):
                shutil.copyfile(os.path.join(res_dir, "logging.cfg"), os.path.join(conf_dir, "logging.cfg"))

            is_first_launch = True
        except Exception as e:
            print(f"Warning: Could not create configuration files: {e}")
    else:
        print("Configuration found")

    # Load configuration into environment variables for GalaxySettings
    # This bridges the gap between the legacy config file and the new GalaxySettings class
    if os.path.isfile(config_file):
        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if 'server' in config:
                server_conf = config['server']

                # Map legacy config keys to new environment variables
                mapping = {
                    'GALAXY_SERVER': 'GALAXY_SERVER',
                    'SERVER_HOST': 'HOST',
                    'SERVER_PORT': 'PORT',
                    'MAX_CONTENT_LENGTH': 'MAX_FILE_SIZE_MB', # Needs conversion
                    'LOG_LEVEL': 'DEBUG' # Approximate mapping
                }

                for conf_key, env_key in mapping.items():
                    if conf_key in server_conf:
                        value = server_conf[conf_key]

                        # Special handling for values
                        if conf_key == 'MAX_CONTENT_LENGTH':
                            # Convert MB to Bytes
                            try:
                                mb_value = int(value)
                                os.environ['MAX_FILE_SIZE'] = str(mb_value * 1024 * 1024)
                            except ValueError:
                                pass
                        elif conf_key == 'LOG_LEVEL':
                            if value.upper() == 'DEBUG':
                                os.environ['DEBUG'] = 'True'
                        else:
                            os.environ[env_key] = value

            print("Loaded configuration from server.cfg into environment")

        except Exception as e:
            print(f"Warning: Error reading configuration file: {e}")

    return is_first_launch

def main():
    """Main entry point."""
    # Setup configuration
    setup_configuration()

    # Initialize server
    try:
        print("Initializing Galaksio Server...")
        server_instance = GalaksioServer()

        # Parse command line args if any, otherwise use defaults/env vars
        import argparse
        parser = argparse.ArgumentParser(description='Galaksio Server')
        parser.add_argument('--host', help='Host to bind to')
        parser.add_argument('--port', type=int, help='Port to bind to')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')

        # Only parse known args to avoid conflicts if needed
        args, _ = parser.parse_known_args()

        # Run server
        print("Starting server...")
        server_instance.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )

    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
