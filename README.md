
```
   __                 _         _                           _ _ 
  / /  __ _ _ __ ___ | |__   __| | __ _     ___   /\  /\___| | |
 / /  / _` | '_ ` _ \| '_ \ / _` |/ _` |   / __| / /_/ / _ \ | |
/ /__| (_| | | | | | | |_) | (_| | (_| |   \__ \/ __  /  __/ | |
\____/\__,_|_| |_| |_|_.__/ \__,_|\__,_|   |___/\/ /_/ \___|_|_|
                                                              
```
# Make a hell for a Lambda! 

A pseudo sHell for communicating with serverless container (by re-invoking commands) - AWS & GCP & Azure for now!

Research, exploit, have fun!

#TODO demo GIF

# Features
- AWS, GCP and Azure compatible!
- Supports tracking current working directory
- File transfer between machine and the Lambda
- Tracking of system reset

# Why

1. Read the research of [Yuval Avrahami](https://unit42.paloaltonetworks.com/gaining-persistency-vulnerable-lambdas/) and wanted to do it myself
2. Verify other providers and create persistency PoCs for them too
3. Get to know a little bit more about serverless internals
4. Reverse shell would be pricey! Longer runtime is equal to the higher prices when using Lambda, so I want to make it as fast as possible
# Installation 

## Dependencies

Client: 
* Python3
* requests
* termcolor  

(optional, could be done manually) AWS Lambda automatic deployment:
* [Terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli)
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) & [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) for your account

(optional, could be done manually) GCP Cloud Functions automatic deployment:
* [Terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli)
* [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

(optional, could be done manually) Azure Functions automatic deployment:
* [Terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli)
* [Azure CLI] (https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

## Installation

### Local client:
```bash 
git clone https://github.com/Djkusik/Lambda-sHell.git
cd Lambda-sHell
pip3 install -r client/requirements.txt
```
    
### AWS Lambda:  
```bash
cd Lambda-sHell/serverless/aws_lambda
# Verify variables.tf for used AWS region and main.tf for AWS profile (using default)
terraform init
terraform apply -auto-approve

# To clean up and delete all of the created AWS resources
terraform destroy -auto-approve
```
Could be also done manually, by uploading ```Lambda-sHell/serverless/aws_lambda/src``` content as Lambda and configuring ApiGateway v2 as a trigger.

### GCP Cloud Function:
```bash
cd Lambda-sHell/serverless/gcp_functions
...
terraform init
terraform apply -auto-approve

# To clean up and delete all of the created AWS resources
terraform destroy -auto-approve
```
Could be also done manually, by uploading ```Lambda-sHell/serverless/gcp_functions/src``` content as Cloud Function and configuring HTTP trigger.

### Azure Functions:
```bash
# TODO
```

### Connecting to the Lambda:
```bash
sHell <lambda-addr> [-fs]
```
# Help
```
   __                 _         _                           _ _ 
  / /  __ _ _ __ ___ | |__   __| | __ _     ___   /\  /\___| | |
 / /  / _` | '_ ` _ \| '_ \ / _` |/ _` |   / __| / /_/ / _ \ | |
/ /__| (_| | | | | | | |_) | (_| | (_| |   \__ \/ __  /  __/ | |
\____/\__,_|_| |_| |_|_.__/ \__,_|\__,_|   |___/\/ /_/ \___|_|_|

A pseudo sHell for communicating with serverless container
         # sHell on local machine.
         # LaRE on serverless container (Lambda, Cloud Functions, Functions)

On a startup, 'whoami' and 'pwd' are executed to gain basic info about container.

# ----------------------------------------------------------------------------------- #

# How to use
         > sHell [-h] [-fs] addr
         > -h   is for printing usage
         > -fs  is for enabling tracking filesystem*
         > addr is URL address for connecting to the LaRE

         * Tracking filesystem means verifying if the container is the same every executed command,
           by checking existance of temporary file in /tmp created on the startup

# Special commands in sHell:
         > 'q' 'quit' 'exit'                    - to exit
         > '!h' '!help'                         - to display this message
         > '!gt <lambda-path> <local-path>'     - to download file to your local machine
         > '!pt <local-path> <lambda-path>'     - to upload file to the serverless container
         > '!curl <address>'                    - to request a resource in case of disabled original curl, uses urllib3 under the hood

# Limitations:
         > File transfer limited to the Lambda's max request/response size (6MB). Bigger files are tried to be compressed.
         > Does not support environment variables
         > Limited support for CWD tracking.
           * Usage of '||' or '&&' breaks tracking, CWD won't be changed then
```
