from .dynamic_url import DynamicUrl
import requests

class Traceos :
    def __init__(self, url='http://jungle.eossweden.org', version='v2') :
        ''' '''
        self._prod_url = url
        self._version = version
        self._dynurl = DynamicUrl(url=self._prod_url, version=self._version)
    
    def get(self, func='', **kwargs) :
        ''' '''
        cmd = eval('self._dynurl.{0}'.format(func))
        url = cmd.create_url()
        print(url)
        return cmd.get_url(url, **kwargs)

    def post(self, func='', **kwargs) :
        ''' '''
        cmd = eval('self._dynurl.{0}'.format(func))
        url = cmd.create_url()
        print(url)
        return cmd.post_url(url, **kwargs)

    def get_transaction(self, trx_id):
        path = 'history.get_transaction'
        params = {'id': trx_id}
        return self.get(path, params=params)
    
    def get_actions(self, options):
        path = 'history.get_actions'
        return self.get(path, params=options)
    
    def get_account(self, account_name):
        path = 'state.get_account'
        json_data = {
            "account_name": account_name
        }
        return self.post(path, params=None, json=json_data)
    
    def check_heath(self):
        path = 'health'
        return self.get(path, params=None)