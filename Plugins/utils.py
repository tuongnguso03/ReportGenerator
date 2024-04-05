import tiktoken
import json
def json_split(string):
    data = json.loads(string.replace("'", '"'))
    ret = {
        "title" : data['report']['title'],
        "introduction" : data['report']['introduction'],
        "body" : data['report']['body'],
        "conclusion" : data['report']['conclusion'],
        "recommendations" : data['report']['recommendations']
    }
    return ret

def token_count(string):
    encoding = tiktoken.get_encoding("cl100k_base")
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens

