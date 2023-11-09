# We use a pymesh base image build with an acceptable python and will add our code to it. For more details, see https://hub.docker.com/_/python
FROM topologicalhurt/pymesh-3.10:v1.1

# We install poetry to generate a list of dependencies which will be required by our application
RUN pip install poetry

COPY . .

# Using poetry, we generate a list of requirements, save them to requirements.txt, and then use pip to install them
RUN poetry install
