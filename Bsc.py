from web3 import Web3
import json


class Bsc:
    chain_id = 56
    endpoint = "https://bsc-dataseed.binance.org/"
    abi_config_path = "./abi/%s.json"
    to_bnb = lambda y, x : float(x) / 1000000000000000000
    to_wei = lambda y, x : int(x * 1000000000000000000)
    def __init__(self, account, private_key):
        self.private_key = private_key
        self.account = account
        self.last_nonce = 0
        self.w3 = Web3(Web3.HTTPProvider(self.endpoint))
        print("BSC connected = %s"%(self.w3.isConnected()))
        print("Using account %s"%(account))
        self.check_balance()

    def load_contract(self, name, address="0x0"):
        data = self.__load_json(name)
        if address == "0x0":
            address = data["address"]
        address = Web3.toChecksumAddress(address)
        contract = self.w3.eth.contract(address=address, abi=data["abi"])

        return contract

    def write_contract_buy(self, draft_txn, draft_bnb_amount, gwei = 5):
        nonce = self.__get_nonce()
        txn = draft_txn.buildTransaction({
            'chainId': self.chain_id,
            'value': Web3.toWei(draft_bnb_amount, 'ether'),
            'gas': 10000000,
            'gasPrice': Web3.toWei(gwei, 'gwei'),
            'nonce': nonce,
            })
        

        return self.__write_contract(txn, gwei)

    def write_contract(self, draft_txn, gwei = 5):
        nonce = self.__get_nonce()
        txn = draft_txn.buildTransaction({
            'chainId': self.chain_id,
            'gas': 10000000,
            'gasPrice': Web3.toWei(gwei, 'gwei'),
            'nonce': nonce,
            })

        return self.__write_contract(txn, gwei)


    
    def check_balance(self):
        balance = self.w3.eth.getBalance(self.account)
        print("Account Balance: %f BNB"%(Web3.fromWei(balance, "ether")))



    def __write_contract(self, txn, gwei):
        signed_txn = self.w3.eth.account.signTransaction(txn, private_key=self.private_key)
        self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print('Transaction sent: %s' % (signed_txn.hash.hex()))

        return signed_txn.hash


    def __load_json(self, name):
        with open(self.abi_config_path % (name)) as f:
            data = json.load(f)

        return data

    def __get_nonce(self):
        self.nonce = self.w3.eth.getTransactionCount(self.account)
        if not (self.nonce > self.last_nonce):
            self.nonce = self.last_nonce + 1
        self.last_nonce = self.nonce

        print('Nonce %s' % (self.nonce))
        return self.nonce
