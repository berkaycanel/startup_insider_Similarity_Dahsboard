import requests
import json
import os
#from dotenv import load_dotenv
#load_dotenv()
ES_URL = 'https://wordpress_staging:J4L3AAGz2NMT@83134a2d1d5e4b0db8824e0209a80600.eu-central-1.aws.cloud.es.io:9243'

def get_domain_tags_new(domain):
    payload = json.dumps({
        'size': 1,
        '_source': [
            'refined_gpt_tags',
            'cb_tags',
            'li_tags',
            'funding_stage',
            'employees',
            'total_funding_amount',
            'wp_tags'
        ],
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            'domain.keyword': domain,
                        }
                    }
                ]
            }
        }
    })
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request('GET', ES_URL + '/domain_crawler/_search', headers=headers, data=payload)
    json_data = json.loads(response.text)
    
    if len(json_data['hits']['hits']) > 0:
        source_data = json_data['hits']['hits'][0]['_source']
        return {
            'refined_gpt_tags': source_data.get('refined_gpt_tags', []),
            'cb_tags': source_data.get('cb_tags', []),
            'li_tags': source_data.get('li_tags', []),
            'funding_stage': source_data.get('funding_stage', 'N/A'),
            'employees': source_data.get('employees', 'N/A'),
            'total_funding_amount': source_data.get('total_funding_amount', 'N/A'),
            'wp_tags': source_data.get('wp_tags', [])
        }
    else:
        return {
            'refined_gpt_tags': [],
            'cb_tags': [],
            'li_tags': [],
            'funding_stage': 'N/A',
            'employees': 'N/A',
            'total_funding_amount': 'N/A',
            'wp_tags': []
        }


def get_related_domains_new(tags, domain, funding_stage, employees, total_funding_amount, boosts=None):
    if boosts is None:
        boosts = {
            
            'refined_gpt_tags': 3.5,
            'cb_tags': 2.5,
            'li_tags': 3.0,
            'funding_stage': 3.0,
            'employees': 2.0,
            'total_funding_amount': 3.0,
            'wp_tags': 2.5
        }

    tags_obj = []
    for tag in tags:
        tags_obj.append({
            'bool': {
                'should': [
                    {'term': {'refined_gpt_tags.keyword': {'value': tag, 'boost': boosts['refined_gpt_tags']}}},
                    {'term': {'cb_tags.keyword': {'value': tag, 'boost': boosts['cb_tags']}}},
                    {'term': {'li_tags.keyword': {'value': tag, 'boost': boosts['li_tags']}}},
                    {'term': {'wp_tags.keyword': {'value': tag, 'boost': boosts['wp_tags']}}}
                ]
            }
        })

    payload = json.dumps({
    'size': 15,
    '_source': [
        'domain',
        'refined_gpt_tags',
        'cb_tags',
        'li_tags',
        'funding_stage',
        'employees',
        'total_funding_amount',
        'wp_tags'
    ],
    'highlight': {
        'fields': {
            'refined_gpt_tags.keyword': {},
            'cb_tags.keyword': {},
            'li_tags.keyword': {},
            'funding_stage': {},
            'employees': {},
            'total_funding_amount': {},
            'wp_tags.keyword': {}
        }
    },
    'query': {
        'bool': {
            'must_not': [
                {
                    'term': {
                        'domain.keyword': domain,
                    }
                }
            ],
            'should': tags_obj + [
                {'match_phrase': {'funding_stage': {'query': funding_stage, 'boost': boosts['funding_stage']}}},
                {'match_phrase': {'employees': {'query': employees, 'boost': boosts['employees']}}},
                {'match_phrase': {'total_funding_amount': {'query': total_funding_amount, 'boost': boosts['total_funding_amount']}}}
            ],
            'minimum_should_match': 2,
            'boost': 1.0
        }
    }
})

    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request('GET', os.getenv('ES_URL') + '/domain_crawler/_search', headers=headers, data=payload)
    json_data = json.loads(response.text)

    print(json.dumps(json_data, indent=4))

    return json_data['hits']['hits']
