
```
 __                           __          __                        __  __          ___    ___      
/\ \                         /\ \        /\ \                      /\ \/\ \        /\_ \  /\_ \     
\ \ \         __      ___ ___\ \ \____   \_\ \     __          ____\ \ \_\ \     __\//\ \ \//\ \    
 \ \ \  __  /'__`\  /' __` __`\ \ '__`\  /'_` \  /'__`\       /',__\\ \  _  \  /'__`\\ \ \  \ \ \   
  \ \ \L\ \/\ \L\.\_/\ \/\ \/\ \ \ \L\ \/\ \L\ \/\ \L\.\_    /\__, `\\ \ \ \ \/\  __/ \_\ \_ \_\ \_ 
   \ \____/\ \__/.\_\ \_\ \_\ \_\ \_,__/\ \___,_\ \__/.\_\   \/\____/ \ \_\ \_\ \____\/\____\/\____\
    \/___/  \/__/\/_/\/_/\/_/\/_/\/___/  \/__,_ /\/__/\/_/    \/___/   \/_/\/_/\/____/\/____/\/____/
                                                                                                    
```
# Make a hell for a Lambda! 

A pseudo sHell for communicating with serverless container (by re-invoking commands) - AWS & GCP for now!

Research, exploit, have fun!

#TODO demo GIF

# Features
- AWS and GCP compatible!
- Supports tracking current working directory
- File transfer between machine and the Lambda
- Tracking of system reset

# Why

1. Read the research of [Yuval Avrahami](https://unit42.paloaltonetworks.com/gaining-persistency-vulnerable-lambdas/) and wanted to do it myself
2. Create server not only for Python runtime
3. Write payloads for RCE/Command Injection for different runtimes
4. Reverse shell would be pricey! Longer runtime is equal to the higher prices when using Lambda, so I want to make it as fast as possible
## Installation 

### Dependencies

Python3, requests, termcolor

### Installation

Client:
```bash 
  git clone https://github.com/Djkusik/Lambda-sHell.git
  cd Lambda-sHell
  pip3 install -r client/requirements.txt
```
    
Lambda:  
#TODO

Usage:
```bash
  python3 sHell.py <lambda-addr> [-fs]
```
#TODO rest of README