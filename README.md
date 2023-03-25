# Asynchronous Backend Framework

## Initial code pull and local environment deployment:
- 1. git clone https://github.com/YSH0313/pacer.git
- 2. Change the MYSQL address in settings.py to your own.

## Operating environment
- Python3.7.2 and above
- Install dependencies in requirements.txt

## Usage
- Use the pacer -p <project_name> command to create a project.
- Use production.py to create an app.
- The application directory contains the created app project.
- Write view functions in the created app.
- The urls.py under the app project is used to store corresponding views and routes.

## Start the service
- Execute runner.py to start the service.

## Start the service in production environment
- Docker can be used to start or other methods, docker startup is recommended.
- You can execute docker-compose up -d in the project root directory.
- The service can be restarted directly by executing reload_server.sh.
- Dockerfile and docker-compose.yml parameters can be adjusted as needed.
