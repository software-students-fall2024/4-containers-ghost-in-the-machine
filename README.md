![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

## Overview
This project is a containerized boyfriend simulator application where users can interact with a virtual boyfriend by speaking into a microphone. The spoken input is transcribed using the Google Cloud Speech-to-Text API, and the transcribed information is processed using the Character API to generate personalized, dynamic boyfriend responses, creating an immersive conversational experience.
 
## Getting Started
Before starting, ensure you have the following installed:
- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.10+
   ```
- brew install ffmpeg
   ```

## `.env` File Setup Instructions
#### `.env` File for Database Connection
In the `web-app` and `machine-learning-client` directory, create a `.env` file and add the following content:
```
MONGO_URI="mongodb+srv://<your_username>:<your_password>@cluster0.0yolx.mongodb.net/fitness_db?retryWrites=true&w=majority"
SECRET_KEY="<your_secret_key>"
```
- Replace `<your_username>` with your MongoDB username.
- Replace `<your_password>` with your MongoDB password.
- Replace `<your_secret_key>` with a unique secret key for your web application.

#### Machine Learning Client - `.env` File for Google Cloud Service
In the `machine-learning-client` directory, create a `.env` file and add the following content:
```
GOOGLE_APPLICATION_CREDENTIALS=”<path_to_your_service_account.json>”
```

This key in your .env file is used to set the path to the Google Cloud Service Account JSON file with all configurations. 

```
GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON=’{
“type”: “<your_type>”,
“project_id”: “<your_project>”,
“private_key_id”: “<your_key_id>”,
“private_key”: “<your_key>”,
“client_email”: “<your_email>”,
“client_id”: “<your_id>”,
“auth_uri”: “<your_auth_uri>”,
“token_uri”: “https://oauth2.googleapis.com/token”,
“auth_provider_x509_cert_url”: “https://www.googleapis.com/oauth2/v1/certs”,
“client_x509_cert_url”: “<your_uri>”,
“universe_domain”: “googleapis.com”
}’
```
- Replace each `<placeholder>` (e.g., `<your_type>`, `<your_project>`) with the corresponding values from your Google Cloud service account.
- To obtain these values, you need to register a Google Cloud service account and download the JSON key file containing the credentials. The path to the JSON file is included in the .env as explained above.


#### Web App - `.env` File for Character API
In the `web-app` `.env` file add the following content with your actual Character API key:
```
SECRET_KEY=”<your_secret_key>”
```



## Run and Configure Code
   
1. First, clone the repository into your preferred IDE or terminal.
   ```
   https://github.com/software-students-fall2024/4-containers-ghost-in-the-machine.git
   cd 4-containers-ghost-in-the-machine
   ```
   
2. Build and start the app using Docker Compose:
   ```
   docker-compose up --build
   ```
   This will start all containers.
3. Open the app in your browser at:
```
   http://localhost:8000
   ```
**Stop all containers:**
 ```
docker-compose stop
```
**Stop and remove containers:**
 ```
docker-compose down
```

## Setup Virtual Environment Instructions

### 1. Clone the Repository

```
git clone https://github.com/software-students-fall2024/4-containers-ghost-in-the-machine.git
cd 4-containers-ghost-in-the-machine
```

### 2. Go to the directory that you want to set virtual environment for

```
cd web-app
```

or

```
cd machine-learning-client
```

### 3. Install pipenv

```
pip install pipenv
```

### 4. Install dependencies

```
pipenv install
```

### 5. Activate the shell

```
pipenv shell
```


## Meet the Team
[sahar][Github](https://github.com/saharbueno)

[toshiHTroyer][Github](https://github.com/toshiHtroyer)

[vernairesl][Github](https://github.com/vernairesl)

[shrayawasti][Github](https://github.com/shrayawasti)


