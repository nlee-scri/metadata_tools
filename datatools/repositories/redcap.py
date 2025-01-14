
import requests
import json
from dataclasses import dataclass
import pandas as pd
import re
from datatools.utils.utils import check_file

class redcap_submissions(): 
    def __init__(self, token): 
        self.token = token
        self.base_url = 'https://redcap.seattlechildrens.org/api/'
    
    def post(self, data: dict, **kwargs): 
        try: 
            r = requests.post(self.base_url,timeout=30, data = data, **kwargs)
            r.raise_for_status()
            print(f'HTTP Status: {r.status_code}')
            return r.json()
        except requests.exceptions.HTTPError as err: 
            raise SystemExit(err)
    
    def create_new_folder(self, folder_name: str, folder_id: str = None): 
        # New folder

        if folder_id is None: 
            folder_id = ''

        data = {
            'token': self.token,
            'content': 'fileRepository',
            'action': 'createFolder',
            'format': 'json',
            'name': folder_name,
            'folder_id': folder_id,
            'returnFormat': 'json'
        }

        result = self.post(data)

        return result
    
    def get_file_repo_list(self): 
        # get list of folders
        data = {
            'token': self.token,
            'content': 'fileRepository',
            'action': 'list',
            'format': 'json',
            'folder_id': '',
            'returnFormat': 'json'
        }

        self.file_repo_list = self.post(data)

        print(self.file_repo_list)
    
    def put_file(self, file_path: str, folder_id: str = None):

        if folder_id is None: 
            folder_id = ''

        # New file
        data = {
            'token':self.token, 
            'content': 'fileRepository', # information needed
            'action': 'import',
            'returnFormat': 'json',
            'folder_id': folder_id # parent
        }
        # upload file
        with open(file_path, 'rb') as f_out: 
            r = self.post(data=data, files={'file':f_out})
            print('HTTP Status: ' + str(r.status_code))
            

@dataclass
class redcap_worker(): 
    """ for working with redcap """
    api_token: str
         
    def get_data(self, data: dict):
        """API call to redcap

        Args:
            content (str): _description_
            token (str): _description_

        Raises:
            SystemExit: _description_

        Returns:
            _type_: _description_
        """
        # get project info
        data = data | {"token": self.api_token,}
        # data = {
            
        #     "content": content,  # information needed
        #     "format": "json",
        #     "returnFormat": "json",
        # }
        try:
            r = requests.post(
                "https://redcap.seattlechildrens.org/api/", data=data, timeout=10
            )
            r.raise_for_status()
            print(f"HTTP Status: {r.status_code}")
            return r.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    def upload_record(self, record:dict, repeat_instruments: bool = False, repeat_instrument_name: str = None, url: str = None): 
        """ Todo: check for existing repeat instruments. For ImmPort """
        if repeat_instruments: 
            record['redcap_repeat_instance'] = 'new'
            record['redcap_repeat_instrument'] = repeat_instrument_name # if adding more instruments
            
        data = json.dumps([record], indent=None)

        fields = {
            'token': self.api_token,
            'content': 'record',
            'action': 'import',
            'format': 'json',
            'type': 'flat',
            'overwriteBehavior': 'normal',
            'forceAutoNumber': 'false',
            'data': data,
            'returnContent': 'count',
            'returnFormat': 'json'
        }

        r = requests.post(url,data=fields)
        print('HTTP Status: ' + str(r.status_code))
        if r.status_code == 200: 
            return r.text
        else: 
            print(r.text)
            raise ValueError('Did not upload record')
    def get_study_records(self, study_id): 
        data = {
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'flat',
            'csvDelimiter': '',
            'records[0]': study_id,
            'rawOrLabel': 'label',
            'rawOrLabelHeaders': 'raw',
            'exportCheckboxLabel': 'false',
            'exportSurveyFields': 'false',
            'exportDataAccessGroups': 'false',
            'returnFormat': 'json'
        }

        result = self.get_data(data)
        cleaned_results = [{k:v for k,v in r.items() if v != ''} for r in result]
        cleaned_results = pd.DataFrame(cleaned_results)
        cleaned_results = cleaned_results.drop(columns=['study_id'])
        cleaned_results = cleaned_results.dropna(how='all', axis = 0)
        print(cleaned_results.info())
        return cleaned_results
    
    def get_file_list(self, folder_id: int): 
        data = {
            'content': 'fileRepository',
            'action': 'list',
            'format': 'json',
            'folder_id': folder_id,
            'returnFormat': 'json'
        }

        result = redcap_worker.get_data(data)
        
        for i, v in enumerate(result): 
            v['parent'] = folder_id
            result[i] = v
        
        return result
    
    def recursive_file_search(self, top_level_folder: int): 
        """ Recursively get the file names for the dataset """
        results = []
        temp = self.get_file_list(top_level_folder)
        for t in temp:
            if 'folder_id' in t:
                id = t.pop('folder_id')
                t['type'] = 'folder'
                t['id'] = id
                
                results.append(t)
                results += self.recursive_file_search(t['id'])
            else: 
                id = t.pop('doc_id')
                t['type'] = 'doc'
                t['id'] = id
                
                results.append(t)
                
        return results
        
class instrument:
    def __init__(self, form_name):
        self.form_name = form_name
        self.fields = []

    def add_field(self, field_name: str):
        field = {
            "field_name": field_name,
            "form_name": self.form_name,
            "section_header": "",
            "field_type": "",
            "field_label": "",
            "select_choices_or_calculations": "",
            "field_note": "",
            "text_validation_type_or_show_slider_number": "",
            "text_validation_min": "",
            "text_validation_max": "",
            "identifier": "",
            "branching_logic": "",
            "required_field": "",
            "custom_alignment": "",
            "question_number": "",
            "matrix_group_name": "",
            "matrix_ranking": "",
            "field_annotation": "",
        }

        self.fields.append(field)


def template_col_mapper(template): 
    mapper = {}
    for word in template['properties'].keys(): 
        if " " in word: 
            continue
        
        new_word = ""
        for i, letter in enumerate(word): 
            if i == 0: 
                new_word += letter.upper()
            else: 
                if letter.isupper(): 
                    new_word += " " + letter 
                else: 
                    new_word += letter
        
        if bool(re.search('id', word, flags=re.IGNORECASE)): 
            new_word = re.sub('id', 'ID', new_word, flags=re.IGNORECASE)
        # print(word, ":", new_word)
        mapper[word] = new_word

    return mapper

def get_template_header(template_path): 
    header = []
    with open(template_path, 'r') as file: 
        while True: 
            line = file.readline()
            if not line or line == '\n': # only new line indicating break. What if space between header and columns? 
                break
            else: 
                header.append(line)
    return header

def create_empty_template(template_path, outfile_path): 
    header = get_template_header(template_path)
    
    # add header
    with open(outfile_path, 'w') as file: 
        file.writelines(header)

def create_txt_file(template_path, outfile_path,  df):
    
    check_file(outfile_path)
    
    headers = get_template_header(template_path)

    # add header
    with open(outfile_path, 'w') as file: 
        file.writelines(headers[:2])

    if 'Column Name' not in list(df.columns): 
        df.insert(0, 'Column Name', None, allow_duplicates=True)

    df.to_csv(outfile_path, sep='\t', index=False, header=True, lineterminator='', mode='a')
    print(f"Data frame shape: {df.shape}\n")
    print(f"Created file: {outfile_path}")
    # return df
    
def get_response_status(response): 
    if response.status_code == 200:
        ticket = response.json()['uploadTicketNumber']
        print(response.content.decode("utf-8"))
        print(ticket)
        return ticket
    else:
        print('Upload failed')
        print(response.text)
        raise Exception

def basic_cleanup(df, mapper, instrument_name): 
    """ For cleaning up dataframes to match the immport templates """
    df.columns = [re.sub(instrument_name, '', t).strip("_") for t in df.columns]
    
    new_col_names = []
    
    for i, c in enumerate(df.columns):
        temp = c.split('_')
        for i2, x in enumerate(temp): 
            if i2 != 0: 
                temp[i2] = ''.join([x[0].upper(), x[1:]])
        
        temp = ''.join(temp)
            
        new_col_names.append(temp)
        
    # print(new_col_names)
    
    df.columns = new_col_names
    # display(df)
    
    for c in mapper.keys():
        if c not in df.columns:
            df[c] = ''
    
    df = df[mapper.keys()]

    df = df.rename(columns=mapper, errors='ignore')

    return df