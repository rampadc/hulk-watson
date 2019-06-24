# Hulk Smash Care with IBM Watson

Example Python service orchestration engine with:

- IBM Watson Assistant
- IBM Watson Discovery
- IBM Watson Tone Analyzer 

When a message is sent to this service by adding to the URL parameter `msg`, the sequence of actions to process request is as follows:

1. Get tones from Watson Tone Analyzer
2. Extract angry tones
3. If angry tone is detected, send Watson Assistant custom context variables `tone_anger_score` between 0 and 1, and a fixed `tone_anger_threshold` specified by an environment variable`TONE_ANGRY_THRESHOLD`. If score is greater than TONE_ANGRY_THRESHOLD, user is deemed angry.
4. If user wants news that mentions 'the hulk', get some news from Watson Discovery.
5. Respond with a JSON that lists all the information gathered above.

## Getting Started

### Prerequisites

Before consuming this service, you need to have Assistant, Discovery and Tone Analyzer instances provisioned on IBM Cloud.

Import `skill-hulk.json` from this repository into Watson Assistant. The default English news collection in Watson Discovery is used.

The remainder of this README assumes you are working within a virtual environment. If you don't have it, run

```.env
pip3 install virtualenv
```

### Installing

Copy `sample.env` to a new `.env` file. Fill out the credentials as needed.

Install the dependencies with

```.env
pip install -r requirements.txt
```

### Run

To run locally, invoke

```.env
python main.py
```

To run locally on CF Local, invoke

```.env
cf local stage hulk-watson
cf local run hulk-watson
```

Unless a different port is specified, an instance will start at http://127.0.0.1/8000.

To send a message to Watson Assistant, try 

```.env
http://127.0.0.1:8000/?msg=I am angry
``` 


## Deployment

To deploy remotely on Cloud Foundry, using IBM Cloud CLI, invoke

```.env
ibmcloud cf push
```

Otherwise, using any other Cloud Foundry providers, invoke

```.env
cf push
```

## License

This project is licensed under the Apache 2.0 License.

