# Use an official AWS Lambda base image for Python
FROM public.ecr.aws/lambda/python:3.12

# Install ssh-keyscan using microdnf (lighter than dnf)
RUN microdnf update -y && \
    microdnf install -y openssh-clients && \
    microdnf clean all && \
    rm -rf /var/cache/yum

# # Install Python dependencies
# COPY ./lambda/recall/requirements.txt ${LAMBDA_TASK_ROOT}
# RUN pip install -r requirements.txt

# # Copy the Python script to the Docker container
# COPY ./lambda/recall/libs ${LAMBDA_TASK_ROOT}/libs
# COPY ./lambda/recall/lambda_function.py ${LAMBDA_TASK_ROOT}

# Install Python dependencies
COPY ./requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the Python script and libraries to the Docker container
COPY ./libs ${LAMBDA_TASK_ROOT}/libs
COPY ./lambda_function.py ${LAMBDA_TASK_ROOT}/lambda_function.py

# Set the working directory to the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Ensure that the Python path includes the libs directory
ENV PYTHONPATH "${LAMBDA_TASK_ROOT}/libs:${PYTHONPATH}"

# Command to run the Python script
CMD ["lambda_function.lambda_handler"]
