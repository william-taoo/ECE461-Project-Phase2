FROM --platform=$BUILDPLATFORM node:18-bullseye

# Set the working directory inside the container
WORKDIR /app

# Install Python 3 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

# Copy package.json and package-lock.json (if available) to the working directory
# COPY package*.json ./

# # Install npm dependencies
RUN  npm install -g typescript

# Install Python dependencies (if you have a requirements.txt file)
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the rest of the application files to the working directory
COPY . .

# COPY .env .
# ENV $(cat .env | xargs)

# Command to run the autograder.py script
# ENTRYPOINT ["python3", "autograder.py"]