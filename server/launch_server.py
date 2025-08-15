import os
import shutil
import argparse
import sys

# This is a hack to make the imports work when running as a module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server import GalaksioServer
from server.resources.galaxy_settings import settings

isFirstLaunch = False
isDocker = False

if not os.path.isfile(os.path.dirname(os.path.realpath(__file__)) + "/conf/server.cfg"):
    print("Configuration not found, creating new settings file")
    conf_dir = os.path.dirname(os.path.realpath(__file__)) + "/conf/"
    res_dir = os.path.dirname(os.path.realpath(__file__)) + "/resources/"
    shutil.copyfile(res_dir + "__init__.py", conf_dir + "__init__.py")
    shutil.copyfile(res_dir + "example_serverconf.cfg", conf_dir + "server.cfg")
    shutil.copyfile(res_dir + "logging.cfg", conf_dir + "logging.cfg")
    isFirstLaunch = True
else:
    print("Configuration found, launching application")

parser = argparse.ArgumentParser(description='Galaksio Server')
parser.add_argument('--host', default=settings.HOST, help='Host to bind to')
parser.add_argument('--port', type=int, default=settings.PORT, help='Port to bind to')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--start', action='store_true', help='Start the server')

# This is needed because the run.sh script passes the --start flag
# and we need to get the other arguments from sys.argv
if '--start' in sys.argv:
    # Filter out the --start argument to not confuse argparse
    filtered_args = [arg for arg in sys.argv[1:] if arg != '--start']
    args = parser.parse_args(filtered_args)

    server = GalaksioServer()
    # The following two properties are not defined in GalaksioServer
    # I will comment them out for now.
    # server.isFirstLaunch = isFirstLaunch
    # server.isDocker = isDocker
    server.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
else:
    print("Galaksio Server")
    print("Use --start to start the server")
    print("Use --help for more options")
