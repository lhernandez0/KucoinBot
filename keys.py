def getKeys(mode):
    if(mode=="sandbox"):
        api_key = ''
        api_secret = ''
        api_passphrase = ''
        sandbox_key = True
    elif(mode=="sandbox_futures"):
        api_key = ''
        api_secret = ''
        api_passphrase = ''
        sandbox_key = True
    elif(mode=="main"):
        api_key = ''
        api_secret = ''
        api_passphrase = ''
        sandbox_key = False
    elif(mode=='futures'):
        api_key = ''
        api_secret = ''
        api_passphrase = ''
        sandbox_key = False
    elif(mode=='sub'):
        api_key = ''
        api_secret = ''
        api_passphrase = ''
        sandbox_key = False
    else:
        return -1
    return api_key, api_secret, api_passphrase, sandbox_key
