FROM public.ecr.aws/lambda/python:3.12

# Install the specified packages
COPY ./lambda/volvo-infleet/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy function code
COPY ./lambda/volvo-infleet/lambda_function.py ${LAMBDA_TASK_ROOT}
COPY ./lambda/volvo-infleet/libs ${LAMBDA_TASK_ROOT}/libs

WORKDIR ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_function.handler" ]