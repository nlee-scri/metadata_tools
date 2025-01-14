import json
import pandas as pd
from glob import glob
from pathlib import Path
from datatools import redcap
from datatools.utils import utils
import re

def json_col_mapper(word):
    """ Using snake case """
    word = utils.remove_special_characters(word)
    word = word.replace(' ', "")
    new_word = ""
    for i, letter in enumerate(word): 
        if i == 0: 
            new_word += letter.lower()
        else: 
            if letter.isupper(): 
                new_word += "" + letter 
            else: 
                new_word += letter
        
        if bool(re.search('id', word, flags=re.IGNORECASE)): 
            new_word = re.sub('id', 'Id', new_word, flags=re.IGNORECASE)

    return new_word


def split_template_sections(template_df: pd.DataFrame, template_name: str): 
    """ Splits the required sections for the template into two parts. Results and metadata
    
    Returns: 
        list: Required columns list
    """
    possible_temp_names = ['Datum', 'MetaData', 'ResultData']
    cols = {}
    for p in possible_temp_names: 
        try: 
            cols[p] = list(template_df.loc[f'{template_name}.{p}', 'properties'].keys())
        except Exception as e: 
            print('Template likley does not exisit: ', p)
    
    req_cols = [v for v in cols.values()]
    
    return req_cols

def add_req_cols(df, req_cols): 
    """ Add required cols to template"""
    # put columns in df
    for c in req_cols: 
        if c not in df.columns: 
            df[c] = None
        
    df = df[req_cols]
    
    return df

def adjust_redcap_cols(df): 
    """ Removing the underscores and snake-case column names"""
    new_cols = []
    for c in df.columns: 
        # print(c.split('_'))
        temp = c.split('_')
        if len(temp) > 1:
            for i,t in enumerate(temp[1:], start=1):
                temp[i] = t[0].upper() + t[1:]
        
        new_cols.append(''.join(temp))
        
    df.columns = new_cols
    return df


def get_templates(immport_temp_dir: str, term:str): 
    # Load templates
    templates = glob(f"{immport_temp_dir}\\json-templates\\{term}")
    temp_names = [Path(t).stem for t in templates]
    # print(temp_names)

    temp_templates = []
    for t in templates:
        with open(t) as file:
            temp = json.load(file)
            temp['template'] = Path(t).stem
            temp_templates.append(temp)

    template_df = pd.DataFrame(temp_templates)
    try: 
        mappings = []
        term = term.strip('*')
        for r in template_df[template_df['template'].str.contains(term)].to_dict('records'): 
            mappings.append(redcap.template_col_mapper(r))

        template_df['mappings']=mappings
    except: 
        pass
    
    template_df['template'] = template_df['template'].str.split('.').apply(lambda x: '.'.join(x[1:]) if len(x) > 1 else x[0])
    
    template_df = template_df.set_index('template')
    template_df = template_df.drop(columns = ['$schema', 'title', 'type'])
    template_df.head()
    
    return template_df

def setup_json_file(templates_df: pd.DataFrame, template_name: str): 
    """ For immport upload"""    
    json_template = {}
    properties = templates_df.loc[template_name, 'properties']
    for k,v in properties.items(): 
        if isinstance(v, dict): 
            if 'enum' in v.keys(): 
                # print(k,v['enum'][0])
                json_template[k] = v['enum'][0]
            elif 'type' in v.keys(): 
                if v['type'] == 'array': 
                    if '$ref' in v['items']: 
                        ref_temp_name = v['items']['$ref'].split('.')[1] # assuming reference template name is the second value
                        # print(ref_temp_name)
                        # ref_temp = templates_df.loc[ref_temp_name, 'properties']
                        json_template[k] =[{k2:"" for k2 in templates_df.loc[ref_temp_name]['properties'].keys()}]
                    else: 
                        json_template[k] = [{k2:"" for k2 in templates_df.loc[template_name]['properties'].keys()}]
            else: 
                json_template[k] = ""
    print(json.dumps(json_template, indent=2))
    return json_template