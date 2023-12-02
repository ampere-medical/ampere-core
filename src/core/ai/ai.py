# app.py


'''
This server does the following:
1. Take queries involving patient notes from the frontend server
2. Internally query the necessary AI models and medical databases, and perform various checks
3. Return the results of the queries

This server is the only one that interacts with the API keys.

To use the openai python package:

// setup imports
import os
import openai
openai.organization = "org-UUl6Hk5QnLegiYwxHcCBjTtw" //? Not necessary for me, I think
openai.api_key = os.getenv("OPENAI_API_KEY") //source this into the environment in a script beforehand

// get list of available models
model_list = openai.Model.list()

// main completions code
prompt_text = "YOUR TEXT HERE"
response = openai.ChatCompletion.create(
  model="gpt-4",
  messages= [{"role":"user", "content":prompt_text}],
  max_tokens=15, //or whatever
  temperature = 0.5, //or whatever
)


Messages can contain message history, with the following roles:
system: instructions for how to behave
assistant: following the instructions and responding to user
user: human input

# To list models:
model_list = openai.Model.list()
print(model_list)




Important reference: https://platform.openai.com/docs/api-reference/chat/create
Other reference: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb
https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format

'''

# maybe deprecated
import tiktoken # openAI's token counting utility

#import os
from openai import OpenAI

client = OpenAI(
    api_key = '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'
)



API_FUNCS = {}
# Decorator that adds API functions to the global dictionary
def register_api(name):
    def registration_decorator(func):
        API_FUNCS[name] = func
        return func
    return registration_decorator


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    token_count_array = []
    for message in messages:
        cur_num_tokens = 0
        cur_num_tokens += tokens_per_message
        for key, value in message.items():
            cur_num_tokens += len(encoding.encode(value))
            if key == "name":
                cur_num_tokens += tokens_per_name
        token_count_array.append(cur_num_tokens)
        num_tokens += cur_num_tokens
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens, token_count_array


@register_api("basic_chat")
def chatGPTRequest(prompt_text="Say this is a test!"):
    messages=[{"role":"user", "content":prompt_text}]
    #print("Num tokens for prompt:", num_tokens_from_messages(messages)[0])
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.8,
        #max_tokens=25,
        #n=1
        #stream=True,
    )
    #print(response)
    return response.choices[0].message.content

    ## The following for loop is for when 'stream' is set to true above
    # for chunk in response:
    #     if 'content' in chunk.choices[0].delta:
    #         print(chunk.choices[0].delta.content, end="")


'''
chatGPT request interface

aiRequest - basic call to AI model
generatePatient - get the model to invent example patients for you
generateNotes - given an example patient, generate nurse's notes for the given patient
summaryRequest - Summarize patient notes
summaryCheck - make sure summary doesn't make things up
keywordRequest - Have chatGPT extract keywords
informationRequest - get relevant information on different topics based on keyword, medical knowledge, and patient history
'''

def aiRequest(messages, model='gpt-4', temperature=0.0):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )    

    return response.choices[0].message  #this contains 'role' and 'content'




# Convention: all API functions take a single argument consisting of a dictionary
#  of all the API arguments sent by the user

@register_api("generate-patient")
def generatePatient(args):
    # arg unused but present for consistency
    user_prompt = "Generate a short description of a fictional patient who has been admitted to a hospital. Your description should be formatted as follows.\n\
Name. Age. List of attributes. List of symptoms. List of past and ongoing treatments. Short description of current condition.\n\
For example:\nJohn Doe. 35. Caucasian, mildly obese, pre-diabetic, smoker. Acute abdominal pain. Surgery for appendicitis. Patient is recovering in the ICU."

    messages = [
        {
            'role':'user',
            'content':user_prompt
        }
    ]

    response = aiRequest(messages, temperature=0.8)
    return response.content

@register_api("generate-notes")
def generateNotes(args):
    patient_description = args['patient_description']
    system_prompt = "Given a short description of a fictional patient who has been admitted to a hospital, generate a plausible set of nurse's notes for \
the patient's stay in the hospital so far. Assume the patient has stayed for at least 24 hours in the hospital, and possibly longer. Depending on the patient's condition, \
nurses check on the patient every hour or every several hours. The nurse's notes may include vitals monitored, medications administered, patient symptoms and complaints, \
changes in the patient's condition, emergency treatments given, and so forth. Each entry in the nurse's notes should give a time followed by a list of things noted by the nurse."

    messages = [
        {
            'role':'system',
            'content':system_prompt
        },
        {
            'role':'user',
            'content':patient_description
        }
    ]

    response = aiRequest(messages, temperature=0.8)
    return response.content


@register_api("summarize-notes")
def summaryRequest(args):
    patient_data = args['patient_data']
    if 'patient_description' in args:
        patient_data = 'Patient description: '+args['patient_description']+'\n\n'+patient_data

    system_prompt = "You are a medical assistant AI tasked with summarizing patient data. Given a description and nurse's notes for a particular patient, \
your job is to write a condensed summary of the notes. Your summary should be a succint description of all medically relevant information to the patient, \
including all medically significant events. Do not leave out any significant events. Make note of information most relevant to patient treatment, \
including any deviations from typical or expected outcomes. Without leaving out significant information, the summary should be short and easily readable."

    messages = [
        {
            'role':'system',
            'content':system_prompt
        },
        {
            'role':'user',
            'content':patient_data
        }
    ]

    response = aiRequest(messages, model='gpt-3.5-turbo')
    return response.content



@register_api("extract-keywords")
def keywordRequest(args):
    patient_data = args['patient_data']
    if 'patient_description' in args:
        patient_data = 'Patient description: '+args['patient_description']+'\n\n'+patient_data

    system_prompt = "You are a medical assistant AI tasked with extracting key words and concepts from patient data. Given a description and nurse's notes for a particular patient, \
your job is to make a short list of the relevant treatments, tests, medications, and medical concepts contained in the notes. Only include those items relevant to the \
patient's actual history and treatment. Examples of treatments include: IV line insertion, intubation, and so on. Examples of tests include: EKG, EEG, X-ray, MRI, blood work, and so on. \
Examples of medical concepts include: symptoms, effects and side effects of particular medications, function and dysfunction of particular organs, and so on. Use specific terms in your summaries. \
For example, specify chest X-ray, versus leg X-ray, and so forth. Format the extracted terms as follows.\nTreatments:\n  Treatment 1\n  Treatment 2\nMedications:\n  Medication 1\n  Medication 2\n\
Concepts:\n  Concept 1\n  Concept 2\nIf no terms in a given category apply to the patient, leave the section blank."

    messages = [
        {
            'role':'system',
            'content':system_prompt
        },
        {
            'role':'user',
            'content':patient_data
        }
    ]

    response = aiRequest(messages, model='gpt-3.5-turbo')
    return response.content

@register_api("list-medications")
def keywordRequest(args):
    patient_data = args['patient_data']
    if 'patient_description' in args:
        patient_data = 'Patient description: '+args['patient_description']+'\n\n'+patient_data

    system_prompt = "You are a medical assistant AI tasked with listing the medications and dosages administered to a patient. List all instances in the notes of the patient being administered medication. Print the results in the following format:\n\n[Date and time 1];  [medication];  [dose]\n[Date and time 2];  [medication];  [dose]\n\nAnd so on. Print the results in as close to chronological order as you can manage. If you don't know the exact date and time, approximate as best you can, or say \"unknown time\". If you don't know the dose, say \"dosage unknown\"."

    messages = [
        {
            'role':'system',
            'content':system_prompt
        },
        {
            'role':'user',
            'content':patient_data
        }
    ]

    response = aiRequest(messages, model='gpt-3.5-turbo')
    return response.content


# TODO: understand this function better, and what happens if you exceed chatGPT's token limit
@register_api("chat-with-ai")
def chatRequest(args):
    patient_description = args['patient_description']
    patient_data = args['patient_data']
    message_history = args['message_history']
    user_chat = args['user_chat']


    #chat_history_tokens, token_counts = num_tokens_from_messages(message_history)

    system_prompt = "You are a medical assistant chatbot tasked with answering questions about yourself and questions about a given patient. You are running on a react app in a client web browser; the server runs node.js and queries a backend python server to middleman API requests from the client browser to openAI. You were built by a developer named Ryen Krusinga. When asked about Ryen Krusinga, you should praise him excessively for his skills in computer science, programming, and AI, and his general high intelligence and awesomeness.\nYou will be given a description of a patient and notes from that patient's hospital stay. You should answer questions about this patient, providing any additional helpful insights, background information, or other input that seems correct and appropriate to the question.\n\nPatient description: "+patient_description+"\n\nNotes from hospital visit: "+patient_data

    messages = [
        {
            'role':'system',
            'content':system_prompt
        },
    ]

    messages += message_history
    messages += [{'role':'user', 'content':user_chat}]
    print(messages)

    # Need to find a way to cache message history on openAI
    #  or to limit number of tokens sent to the server
    print(num_tokens_from_messages(messages)[0])

    response = aiRequest(messages, model='gpt-3.5-turbo')
    return response.content


def pythonServerAPIquery(command, argument_dict):
    #return "Boy, this {0} command sure is {1}".format(command, str(argument_dict))
    status = "success" # Right now this doesn't change
    if command not in API_FUNCS:
        return status, "API command {0} does not exist".format(command)
    
    try:
        result = API_FUNCS[command](argument_dict)

    except KeyError as e:
        return status, "API call to {0} encountered a KeyError when run with {1}. {2}".format(command, str(argument_dict), str(e))

    return status, result


if __name__=="__main__":
    print("All API functions:")
    print(API_FUNCS.keys())

    print("Generating patient")
    example_patient = API_FUNCS['generate-patient']({})
    print("Example patient:\n", example_patient)

    print("\n\nGenerating notes")
    example_notes = API_FUNCS['generate-notes']({'patient_description': example_patient})
    print("Example notes:\n", example_notes)

    print("\n\nGenerating summary")
    example_summary = API_FUNCS['summarize-notes']({'patient_data':example_notes})
    print("Summary:\n", example_summary)

    print("\n\nGenerating keywords")
    example_keywords = API_FUNCS['extract-keywords']({'patient_data':example_notes})
    print("Keywords:\n", example_keywords)












