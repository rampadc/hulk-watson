########################################################################################################################
# Imports
########################################################################################################################
from starlette.applications import Starlette
from starlette.responses import JSONResponse
import uvicorn
from ibm_watson import AssistantV1, DiscoveryV1, ToneAnalyzerV3
from textwrap import shorten
from ibm_watson.assistant_v1 import MessageInput
from ibm_watson.tone_analyzer_v3 import ToneInput
from dotenv import load_dotenv
import os


########################################################################################################################
# Load environment variables
########################################################################################################################
load_dotenv(verbose=True)
tone_anger_threshold = os.getenv('TONE_ANGRY_THRESHOLD')


########################################################################################################################
# Watson Assistant related code
# - version of assistant is dependent on skill version
########################################################################################################################
assistant = AssistantV1(
    version=os.getenv('ASSISTANT_API_VERSION'),
    url=os.getenv('ASSISTANT_IAM_URL'),
    iam_apikey=os.getenv('ASSISTANT_IAM_API_KEY')
)
assistant_workspace_id = os.getenv('ASSISTANT_WORKSPACE_ID')


def assistant_send_text(text):
    return assistant.message(
        workspace_id=assistant_workspace_id,
        input=MessageInput(
            message_type='text',
            text=text
        )
    ).get_result()


def assistant_send_angry_tone(tones):
    anger_tone = get_angry_tone(tones)
    response = {}
    if len(anger_tone) > 0:
        # Create a simple assistant context
        # You would want to keep a global context and keep track of it throughout the conversation
        # https://github.com/watson-developer-cloud/python-sdk/tree/master/examples/assistant_tone_analyzer_integration
        assistant_context = {
            "tone_anger_score": anger_tone[0]['score'],
            "tone_anger_threshold": tone_anger_threshold
        }

        response = assistant.message(assistant_workspace_id, context=assistant_context).get_result()

    if 'output' in response:
        return response


########################################################################################################################
# Watson Discovery related code
########################################################################################################################
discovery = DiscoveryV1(
    version=os.getenv('DISCOVERY_API_VERSION'),
    url=os.getenv('DISCOVERY_IAM_URL'),
    iam_apikey=os.getenv('DISCOVERY_IAM_API_KEY')
)
discovery_environment_id = os.getenv('DISCOVERY_ENVIRONMENT_ID')
discovery_collection_id = os.getenv('DISCOVERY_COLLECTION_ID')


def discovery_query(query):
    response = discovery.query(
        environment_id=discovery_environment_id,
        collection_id=discovery_collection_id,
        query=query,
        return_fields='text'
    ).get_result()
    return response['results']


def check_if_news(message):
    if 'get_news' in message['context']:
        if message['context']['get_news'] == True:
            return True
    return False


def format_discovery_output(results):
    results = list(map(lambda r: {
        "text": shorten(r['text'], width=80),
        "score": r['result_metadata']['score']
    }, results))

    return results


########################################################################################################################
# Watson Tone Analyzer related code
########################################################################################################################
tone_analyser = ToneAnalyzerV3(
    version=os.getenv('TONE_ANALYSER_API_VERSION'),
    url=os.getenv('TONE_ANALYSER_IAM_URL'),
    iam_apikey=os.getenv('TONE_ANALYSER_IAM_API_KEY')
)


def tones_get(utterances):
    return tone_analyser.tone(ToneInput(utterances), content_type='text/plain').get_result()


def get_angry_tone(tones):
    tones = tones['document_tone']['tones']
    # transform tones array to pre-set Watson Assistant context variables
    anger_tone = [tone for tone in tones if 'anger' in tone['tone_id']]
    return anger_tone


def check_if_angry(tones):
    angry_tone = get_angry_tone(tones)
    if len(angry_tone) > 0:
        return True
    else:
        return False


########################################################################################################################
#
# Start a REST API server
#
# message(request) accepts a single URL parameter 'msg' to be sent to a Watson Assistant instance
#
# Sequence of actions to process request:
#   1. Get tones from Watson Tone Analyzer
#   2. Extract angry tones
#   3. If angry tones are detected, send Watson Assistant a custom context variable 'tone_anger_score' with score
#      between 0 and 1. If score is greater than TONE_ANGRY_THRESHOLD, user is deemed angry.
#   4. If user wants news that mentions 'the hulk', get some news from Watson Discovery.
#   5. Respond with a JSON that lists all the information gathered above.
#
########################################################################################################################
app = Starlette(debug=False)


@app.route('/')
async def message(request):
    message_to_assistant = request.query_params['msg']

    assistant_response = assistant_send_text(text=message_to_assistant)
    hulk_news = []

    # Get tones from Watson Tone Analyzer
    tones = tones_get(message_to_assistant)
    anger_tones = get_angry_tone(tones)

    if check_if_angry(tones):
        assistant_response = assistant_send_angry_tone(tones)

    if check_if_news(assistant_response):
        results = discovery_query('the hulk')
        hulk_news = format_discovery_output(results)

    return JSONResponse({
        'input': message_to_assistant,
        'tones': tones,
        'anger_tones': anger_tones,
        'is_angry': check_if_angry(tones),
        'intents': assistant_response['intents'],
        'hulk_news': hulk_news,
        'response': assistant_response['output']['text'][0]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT') or 8000)
    uvicorn.run(app, host='0.0.0.0', port=port)
