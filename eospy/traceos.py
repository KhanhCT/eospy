from .dynamic_url import DynamicUrl

class Traceos :
    def __init__(self, url='https://eos.hyperion.eosrio.io', version='v1') :
        ''' '''
        self._prod_url = url
        self._version = version
        self._dynurl = DynamicUrl(url=self._prod_url, version=self._version)
    
    def get(self, func='', **kwargs) :
        ''' '''
        cmd = eval('self._dynurl.{0}'.format(func))
        url = cmd.create_url()
        return cmd.get_url(url, **kwargs)

    def post(self, func='', **kwargs) :
        ''' '''
        cmd = eval('self._dynurl.{0}'.format(func))
        url = cmd.create_url()
        return cmd.post_url(url, **kwargs)

    def get_transaction(self, trx_id):
        path = 'history.get_transaction'
        json = {'id': trx_id}
        return self.post(path, params=None, json=json)
    
    def get_actions(self, account_name, options):
        path = 'history.get_actions'
        json_data = {
            "account_name": account_name
        }
        json_data.update(options)
        print(json_data)
        return self.post(path, params=None, json=json_data)
    
    def check_heath(self):
        path = 'health'
        try:
            result = self.get(path=path)
            if result.status_code == 200:
                return True, None
            return False, response.json()
        except Exception as ex:
            err = 'request to {} failed {}'.format(assets_url, e)
            return False, err