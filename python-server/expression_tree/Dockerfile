# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# copy the requirements file into the image
COPY ./requirements.txt /python-server/requirements.txt

# Set the working directory in the container
WORKDIR /python-server

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /python-server

# Make port 5000 available to the world outside this container
EXPOSE 9095

ENTRYPOINT [ "python" ]

# Run app.py when the container launches
CMD ["app.py"]