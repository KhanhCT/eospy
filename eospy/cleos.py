#
# cleos.py
#

from .dynamic_url import DynamicUrl
from .keys import EOSKey, check_wif
from .signer import Signer
from .keosd import Keosd
from .utils import sig_digest, parse_key_file, sha256
from .types import EOSEncoder, Transaction, PackedTransaction, Abi
from .exceptions import (EOSKeyError, EOSMsigInvalidProposal, EOSSetSameAbi, EOSSetSameCode)
import json
import os
from binascii import hexlify
import datetime as dt
import copy

class Cleos :
    
    def __init__(self, url='http://localhost:8888', keosd_url = None, version='v1') :
        ''' '''
        self._prod_url = url
        self._version = version
        self._keosd_url = keosd_url
        self._keosd = Keosd(url=self._keosd_url)
        self._dynurl = DynamicUrl(url=self._prod_url, version=self._version)
    
    #####
    # private functions
    #####

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

    #####
    # get methods
    #####
    def get_info(self, timeout=30) :
        ''' '''
        return self.get('chain.get_info', timeout=timeout)

    def get_chain_lib_info(self, timeout=30) :
        ''' '''
        chain_info = self.get('chain.get_info', timeout=timeout)
        lib_info = self.get_block(chain_info['last_irreversible_block_num'], timeout=timeout)
        return chain_info, lib_info
        
    def get_block(self, block_num, timeout=30) :
        ''' '''
        return self.post('chain.get_block', params=None, json={'block_num_or_id' : block_num}, timeout=timeout)
        
    def get_account(self, acct_name, timeout=30) :
        ''' '''
        return self.post('chain.get_account', params=None, json={'account_name' : acct_name}, timeout=timeout)

    def get_code(self, acct_name, code_as_wasm=True, timeout=30) :
        ''' '''
        return self.post('chain.get_code', params=None, json={'account_name':acct_name, 'code_as_wasm':code_as_wasm}, timeout=timeout)
    
    def get_accounts(self, public_key, timeout=30) :
        ''' '''
        return self.post('history.get_key_accounts', params=None, json={'public_key':public_key}, timeout=timeout)

    def get_abi(self, acct_name, timeout=30) :
        ''' '''
        return self.post('chain.get_abi', params=None, json={'account_name' : acct_name}, timeout=timeout)

    def get_raw_abi(self, acct_name, timeout=30) :
        ''' '''
        return self.post('chain.get_raw_abi', params=None, json={'account_name' : acct_name}, timeout=timeout)
        
    def get_actions(self, acct_name, pos=-1, offset=-20, timeout=30) :
        '''
        POST /v1/history/get_actions
        {"account_name":"eosnewyorkio","pos":-1,"offset":-20}
        '''
        json={'account_name' : acct_name, "pos" : pos, "offset" : offset}
        return self.post('history.get_actions', params=None, json=json, timeout=timeout)

    def get_currency(self, code='eosio.token', symbol='EOS', timeout=30) :
        '''
        POST /v1/chain/get_currency_stats HTTP/1.0
        {"json":false,"code":"eosio.token","symbol":"EOS"}
        '''
        json={'json':False, 'code':code, 'symbol':symbol}
        return self.post('chain.get_currency_stats', params=None, json=json, timeout=timeout)

    def get_currency_balance(self, account, code='eosio.token', symbol='EOS', timeout=30) :
      '''
      POST /v1/chain/get_currency_balance HTTP/1.0
      {"account":"eosio","code":"eosio.token","symbol":"EOS"}
      '''
      json={'account':account, 'code':code, 'symbol':symbol}
      return self.post('chain.get_currency_balance', params=None, json=json, timeout=timeout)

    def get_currency_stats(self, code, symbol, timeout=30) :
        return self.post('chain.get_currency_stats', json={'code':code, 'symbol':symbol})
    
    def get_servants(self, acct_name, timeout=30) :
        ''' '''
        return self.post('account_history.get_controlled_accounts', params=None, json={'controlling_account':acct_name}, timeout=timeout)

    def get_transaction(self, trans_id, timeout=30) :
        '''
        POST /v1/history/get_transaction
        {"id":"abcd1234"}
        '''
        return self.post('history.get_transaction', params=None, json={'id': trans_id}, timeout=timeout)

    def get_table(self, code, scope, table, index_position='',key_type='', lower_bound='', upper_bound='', limit=10, timeout=30) :
        '''
        POST /v1/chain/get_table_rows
        {"json":true,"code":"eosio","scope":"eosio","table":"producers","index_position":"","key_type":"name","lower_bound":"","upper_bound":"","limit":10}
        '''
        json = {"json":True, "code":code, "scope":scope, "table":table, "key_type":key_type, "index_position":index_position, "lower_bound": lower_bound, "upper_bound": upper_bound, "limit": limit}
        return self.post('chain.get_table_rows', params=None, json=json, timeout=timeout)

    def get_producers(self, lower_bound='', limit=50, timeout=30) :
        '''
        POST /v1/chain/get_producers HTTP/1.0
        {"json":true,"lower_bound":"","limit":50}
        '''
        return self.post('chain.get_producers', params=None, json={'json':True, 'lower_bound':lower_bound, 'limit':limit}, timeout=timeout)

    #####
    # set
    #####

    def set_abi(self, account, permission, abi_file, key, broadcast=True, timeout=30):
        current_abi = Abi(self.get_abi(account)['abi'])
        current_sha = sha256(current_abi.get_raw().encode('utf-8'))
        with open(abi_file) as rf:
            abi = json.load(rf)
            new_abi = Abi(abi) 
            # hex_abi = hexlify(abi)
            new_sha = sha256(new_abi.get_raw().encode('utf-8'))
            if current_sha == new_sha:
                raise EOSSetSameAbi()
            # generate trx
            arguments = {
                "account": account,  
                "abi": new_abi.get_raw()
            }
            payload = {
                "account": "eosio",
                "name": "setabi",
                "authorization": [{
                    "actor": account,
                    "permission": permission,
                }],
            }
            # Converting payload to binary
            data = self.abi_json_to_bin(payload['account'], payload['name'], arguments)
            # Inserting payload binary form as "data" field in original payload
            payload['data'] = data['binargs']
            trx = {"actions": [payload]}
            sign_key = EOSKey(key)
            return self.push_transaction(trx, sign_key, broadcast=broadcast)
    


    def set_code(self, account, permission, code_file, key, broadcast=True, timeout=30):
        current_code = self.get_code(account)
        # print(current_code)
        # print(type(current_code))
        current_sha = current_code['code_hash']
        with open(code_file, 'rb') as rf:
            wasm = rf.read()
            hex_wasm = hexlify(wasm)
            new_sha = sha256(hex_wasm)
            if current_sha == new_sha:
                raise EOSSetSameCode()
            # generate trx
            arguments = {
                "account": account,
                "vmtype": 0,
                "vmversion": 0,
                "code": hex_wasm.decode('utf-8')
            }
            payload = {
                "account": "eosio",
                "name": "setcode",
                "authorization": [{
                    "actor": account,
                    "permission": permission,
                }],
            }
            # Converting payload to binary
            data = self.abi_json_to_bin(payload['account'], payload['name'], arguments)
            # Inserting payload binary form as "data" field in original payload
            payload['data'] = data['binargs']
            trx = {"actions": [payload]}
            sign_key = EOSKey(key)
            return self.push_transaction(trx, sign_key, broadcast=broadcast)
    
    def lock_wallet(self, wallet_name, timeout=30):
        try:
            return self._keosd.lock_wallet(wallet_name=wallet_name, timeout=timeout)
        except:
            pass
    
    def unlock_wallet(self, wallet_name, password, timeout=30):
        try:
            return self._keosd.unlock_wallet(wallet_name=wallet_name, password=password, timeout=timeout)
        except Exception as ex:
            print("Wallet is already unlocked!")
            pass
        
    #####
    # transactions
    #####
    def push_transaction(self, transaction, keys, broadcast=True, compression='none', timeout=60):
        ''' parameter keys can be a list of WIF strings or EOSKey objects or a filename to key file'''
        chain_info,lib_info = self.get_chain_lib_info()

        if 'expiration' not in transaction :
            transaction['expiration'] = str((dt.datetime.utcnow() + dt.timedelta(seconds=30)).replace(tzinfo=pytz.UTC))
        if 'ref_block_num' not in transaction :
            transaction['ref_block_num'] = chain_info['last_irreversible_block_num'] & 0xFFFF
        if 'ref_block_prefix' not in transaction :
            transaction['ref_block_prefix'] = lib_info['ref_block_prefix']
        trx_data = copy.deepcopy(transaction)
        transaction['expiration'] = str(transaction['expiration'])
        trx = Transaction(transaction, chain_info, lib_info)
        #encoded = trx.encode()
        # sign the transaction
        signatures = []
        # if os.path.isfile(keys):
        #      keys = parse_key_file(keys, first_key=False)

        digest = sig_digest(trx.encode(), chain_info['chain_id'])
        if not isinstance(keys, list):
            if isinstance(keys, Signer):
                pass
            elif isinstance(keys, str):
                pass
            else:
                raise EOSKeyError('Must pass a class that extends the eospy.Signer class')
            keys = [keys]
        pub_keys = []

        for key in keys :
            if isinstance(key, str):
                try :
                    k = EOSKey(key)
                    signatures.append(k.sign(digest))
                except Exception as ex:
                    # public key
                    pub_keys.append(key)
            elif isinstance(key, Signer) :
                signatures.append(key.sign(digest))
            else:
                raise EOSKeyError('Must pass a class that extends the eospy.Signer class')
        
        if len(signatures) == 0:
            # sign transaction:
            if 'signatures' not in trx_data :
                trx_data['signatures'] = []
            import pytz
            utc_time = trx_data['expiration'].astimezone(pytz.UTC)
            trx_data['expiration']=str(utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f"))
            sign_data = [
                trx_data,
                pub_keys,
                chain_info['chain_id']
            ]
            # data = ','.join(str(e) for e in sign_data)
            # sign_data="'[{}]'".format(data)
            signed_data = self._keosd.sign(sign_data=sign_data, timeout=30)
            if 'signatures' in signed_data:
                signatures = signed_data['signatures']
        # build final trx
        final_trx = {
                'compression' : compression,
                'transaction' : trx.__dict__,
                'signatures' : signatures
        }
        data = json.dumps(final_trx, cls=EOSEncoder)
        if broadcast :
            return self.post('chain.push_transaction', params=None, data=data, timeout=timeout)
        return data
    
    def push_block(self, timeout=30) :
        raise NotImplementedError
        
    #####
    # bin/json 
    #####
    
    def abi_bin_to_json(self, code, action, binargs, timeout=30) :
        ''' '''
        json = {'code':code, 'action':action, 'binargs': binargs}
        return self.post('chain.abi_bin_to_json', params=None, json=json, timeout=timeout)

    def abi_json_to_bin(self, code, action, args, timeout=30) :
        ''' '''
        json = {'code':code, 'action':action, 'args': args}
        return self.post('chain.abi_json_to_bin', params=None, json=json, timeout=timeout)
        
    #####
    # create keys
    #####

    def create_key(self) :
        ''' '''
        k = EOSKey()
        return k
        
    #####
    # multisig
    #####
    
    def multisig_review(self, proposer, proposal):
        ''' ''' 
        review = []
        prop = self.get_table(code="eosio.msig", scope=proposer, table="proposal", lower_bound=proposal, limit=1)
        if prop['rows'] :
            for row in prop['rows']:
                packed = PackedTransaction(row['packed_transaction'], self)
                trx = packed.get_transaction()
                p = {
                    "proposer": proposer,
                    "proposal_name": proposal,
                    "transaction_id": packed.get_id(),
                    "packed_transaction": row['packed_transaction'],
                    "transaction": trx,
                }
                review = p
        else:
            raise EOSMsigInvalidProposal("{} is not a valid proposal".format(proposal))
        # 
        return review
                
        
    #####
    # system functions
    #####

    def vote_producers(self, voter, proxy, producers) :
        return self.get('chain.abi_json_to_bin', params=None,json={"voter":voter, "proxy":proxy,"producers":producers})


    def create_account(self, creator, creator_privkey, acct_name, owner_key, 
                       active_key='', stake_net='1.0000 EOS', stake_cpu='1.0000 EOS', ramkb=8, permission='active', 
                       transfer=False, broadcast=True, timeout=30) :
        ''' '''

        # check account doesn't exist
        try : 
            self.get_account(acct_name)
            #print('{} already exists.'.format(acct_name))
            raise ValueError('{} already exists.'.format(acct_name))
        except: 
            pass
        if not active_key :
            active_key = owner_key
        # create newaccount trx
        owner_auth = {
                "threshold": 1,
                "keys": [{
                    "key": owner_key,
                    "weight": 1
                }],
                "accounts": [],
                "waits": []
            }
        active_auth ={
                "threshold": 1,
                "keys": [{
                    "key": active_key,
                    "weight": 1
                } ],
                "accounts": [],
                "waits": []
            }
        print({
                'creator' : creator, 
                'name' : acct_name, 
                'owner' : owner_auth, 
                'active' : active_auth
        })
        
        newaccount_data = self.abi_json_to_bin('eosio', 'newaccount',{'creator' : creator, 'name' : acct_name, 'owner': owner_auth, 'active':active_auth})
        print(newaccount_data)
        newaccount_json = {
            'account' : 'eosio',
            'name' : 'newaccount',
            'authorization' : [
            {
                'actor' : creator,
                'permission' : permission
            } ],
            'data' : newaccount_data['binargs']
        }
        # create buyrambytes trx
        buyram_data = self.abi_json_to_bin('eosio', 'buyrambytes', {'payer':creator, 'receiver':acct_name, 'bytes': ramkb*1024})
        buyram_json = {
            'account' : 'eosio',
            'name' : 'buyrambytes',
            'authorization' : [
                {
                    'actor' : creator,
                    'permission' : permission
                } ],
            'data' : buyram_data['binargs']
        }
        # create delegatebw
        delegate_data = self.abi_json_to_bin('eosio', 'delegatebw', 
            {'from': creator, 'receiver': acct_name, 'stake_net_quantity':stake_net, 'stake_cpu_quantity': stake_cpu, 'transfer': transfer })
        delegate_json = {
            'account' : 'eosio',
            'name' : 'delegatebw',
            'authorization' : [
                {
                    'actor' : creator,
                    'permission' : permission
                } ],
            'data' : delegate_data['binargs']
        }

        trx = {"actions":
            [newaccount_json, buyram_json, delegate_json]
        }
        # push transaction
        return self.push_transaction(trx, creator_privkey, broadcast=broadcast, timeout=timeout)

    def register_producer(self) :
        raise NotImplementedError()

