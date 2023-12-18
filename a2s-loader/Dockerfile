FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# add requirements first to speed up docker builds
ADD requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make sure venv is not in docker image
RUN rm -rf venv

# run main.py
CMD ["python3", "main.py"]