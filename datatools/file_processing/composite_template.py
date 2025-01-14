def table_sheet_cleanup(df):
    start = 0
    try: 
        start = df[df.iloc[:,0] == 'Column Name'].index.tolist()[0]
        print(start)
    except: 
        print('Could not find `Column Name`')
        return df
    
    if start is None or start == 0: 
        return df
    
    df.columns = df.iloc[start, :]
    df = df.iloc[start+1:, :].copy()
    df = df.dropna(axis=1, how='all').reset_index(drop = True)
    return df