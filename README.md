# Collections Transformer 0.1

LLM-powered platform designed to assist users working with collections and datasets. This repository contains the preliminary design of an open LLM-based platform to assess collections in the GLAM sector. Code developed as part of the project "Transforming Collections" undertaken at UAL "Towards a National Collection (TaNC)".

Version of the website is currently active at:  
https://collectionstransforming.com/

Ubuntu 22.04.1 LTS  
AMD EPYC 7713 64-Core Processor  
Linode Akamai Cloud  



## Application Setup

```bash
cd server/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt



```

See `server/requirements.txt` and `client/package.json` for a full set of dependencies. Authentication uses Auth0. You can use an existing Auth0 Tenant. Create `.env` files, the following keys are needed.

```
NEXT_PUBLIC_SERVER_URL = ""
AUTH0_SECRET = "{AUTH0 SECRET}"
AUTH0_ISSUER_BASE_URL = "{YOUR TENANT URL}"
AUTH0_CLIENT_ID = "{AUTH0 CLIENT ID}"
AUTH0_CLIENT_SECRET = "{AUTH0 CLIENT SECRET}"
AUTH0_DOMAIN = "{YOUR TENANT URL}"
```

Models used for inference are gpt4-o for OpenAI API. Alter the keys on the environment files respectively. For Azure the user might add Endpoints via Azure AI Studio.


## Useful MongoDB commands
```
$ mongosh
$ use my_database
$ show collections
# Inspect dataset by name
$ db.dataset.find({"name": "set_1"})
# Count datasets
$ db.dataset.countDocuments()
```

