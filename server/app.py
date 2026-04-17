from api import create_app
from gevent.pywsgi import WSGIServer
import argparse


def app(model="dual", port=8080):
    """
    Initialize the server with specified model configuration.
    
    Args:
        model (str): Model configuration ("dual" for Ollama+Blip2, "ollama", "blip2")
        port (int): Port to run the server on
    """
    http_server = WSGIServer(("0.0.0.0", port), create_app(model))
    http_server.serve_forever() 

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", action="store", default="dual")
parser.add_argument("-p", "--port", action="store", default=8080)
parser.add_argument("-r", "--reload", action="store", default="False")
args, unknown = parser.parse_known_args()
model = args.model

if __name__ == '__main__':
    port = int(args.port)
    reload = str(args.reload).lower() == "true"

    app = create_app(args.model)
    # Disable reloader to prevent process from exiting in terminal
    app.run(debug=True, port=port, use_reloader=False, host='0.0.0.0')


