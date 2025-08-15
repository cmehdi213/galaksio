<div class="imageContainer" style="" >
    <img src="galaksio_logo.png" title="Galaksio logo." style=" height: 70px !important; margin-bottom: 20px; ">
</div>

# Installing Galaksio

This guide will walk you through the process of setting up your own instance of Galaksio.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python**: 3.9 or later.
- **git**: For cloning the repository.
- A modern web browser (e.g., Chrome, Firefox, Safari, Edge).

## Recommended Installation: Local Setup

Due to recent issues with Docker Hub rate limiting, the recommended way to install Galaksio is to run it locally. This gives you more control over the environment and avoids potential Docker-related issues.

### 1. Clone the Repository

First, clone the Galaksio repository from GitHub:

```bash
git clone https://github.com/cmehdi213/galaksio.git
cd galaksio
```

### 2. Install Dependencies

The application requires several Python packages. You can install them using `pip`:

```bash
pip install -r requirements.txt
```
This will install all the necessary dependencies, including `Flask`, `BioBlend`, and others. The unused `fpdf` and `fpdf2` dependencies have been removed.

### 3. Install the Application

Install the application in editable mode. This allows you to make changes to the code without having to reinstall the package.

```bash
pip install -e .
```

### 4. Run the Server

You can now start the Galaksio server by running the `run.sh` script located in the `server` directory:

```bash
cd server
./run.sh --start
```

The server will be available at [http://localhost:8081/](http://localhost:8081/).

## Docker Installation (Not Recommended at this time)

While Docker provides a convenient way to deploy applications, there are currently issues with Docker Hub's rate limiting that can make it difficult to pull the necessary base images. For this reason, the local installation is recommended.

If you still wish to proceed with Docker, you can use the provided `docker-compose.yml` file. Please note that you may encounter rate-limiting errors.

```bash
# This may fail due to Docker Hub rate limits
sudo docker compose up --build
```

## First Configuration

By default, Galaksio is configured to work with the official [Galaxy](https://usegalaxy.org) instance. This and other options can be customized through the web application after the first launch. You will be prompted to configure the main settings when you first access your Galaksio instance.
