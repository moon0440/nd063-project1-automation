from PyInquirer import style_from_dict, Token, prompt, Separator
import boto3


def get_delivery_options(answers):
    options = ['bike', 'car', 'truck']
    if answers['size'] == 'jumbo':
        options.append('helicopter')
    return options


style = style_from_dict({
    Token.Separator: '#6C6C6C',
    Token.QuestionMark: '#FF9D00 bold',
    # Token.Selected: '',  # default
    Token.Selected: '#5F819D',
    Token.Pointer: '#FF9D00 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#5F819D bold',
    Token.Question: '',
})


def region_choices(answers):
    country_code = 'us'
    r = boto3.client('ec2').describe_regions()
    return [x['RegionName'] for x in r['Regions'] if
            x['RegionName'].startswith(country_code) and x['RegionName'] != answers.get('primary_region')]


aws_region_setup = [
    {
        'type': 'list',
        'name': 'primary_region',
        'message': 'Select Primary AWS Region:',
        'choices': region_choices
    },
    {
        'type': 'list',
        'name': 'secondary_region',
        'message': 'Select Secondary AWS Region:',
        'choices': region_choices
    },
    {
        'type': 'confirm',
        'message': 'Deployment with the information above?',
        'name': 'continue',
        'default': True,
    },
]
