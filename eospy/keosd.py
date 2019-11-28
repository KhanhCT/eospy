from .dynamic_url import DynamicUrl
import requests

class Keosd :
    def __init__(self, url='http://localhost:8889', version='v1') :
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
    
    def unlock_wallet(self, wallet_name, password, timeout):
        data = "[\"" + wallet_name + "\",\"" + password + "\"]"
        return self.post('wallet.unlock', data=data, timeout=timeout)

    def lock_wallet(self, wallet_name, timeout):
        return self.post('wallet.lock', data=wallet_name, timeout=timeout)
    
    def set_timeout(self, timeout):
        return self.post('wallet.timeout', data=timeout, timeout=30)

    def sign(self, sign_data, timeout=30):
        return self.post('wallet.sign_transaction', params=None, json=sign_data, timeout=timeout)
