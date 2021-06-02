from web3 import Web3
from datetime import datetime, timedelta
import time
import json, Bsc


class PancakeRouter:
    bnb=Web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
    def __init__(self, bsc, gwei = 7, normal_gwei = 7):
        self.bsc = bsc
        self.gwei = 5
        self.normal_gwei = normal_gwei
        print("Gwei for swapping: %d, for other action: %d"%(gwei, normal_gwei))
        self.contract = bsc.load_contract(type(self).__name__)

    def swap_from_bnb(self, draft_bnb_amount, target, slippage, fair_launch=False, sell=False):
        print("Target to buy %0.2f BNB. current slippage: %0.0f%%"%(draft_bnb_amount, slippage * 100))
        target = Web3.toChecksumAddress(target)
        path = [self.bnb, target]
        bnb_amount = self.bsc.to_wei(draft_bnb_amount)

        check_amount = self.__check_amount(bnb_amount, path)

        # exit if LP not ready?
        if not(check_amount[0] and check_amount[1] > 0):
            return False, 0



        try:
            amount_to_swap = int(check_amount[1]*(1-slippage))
            if fair_launch:  amount_to_swap = 0
            draft_txn = self.contract.functions.swapETHForExactTokens(amount_to_swap, 
                                                            path, 
                                                            self.bsc.account, 
                                                            int(self.__deadline()))
            print('Swaping %0.2f token for %f BNB' % (self.bsc.to_bnb(amount_to_swap), draft_bnb_amount))
            hash = self.bsc.write_contract_buy(draft_txn, draft_bnb_amount, self.gwei)
        except Exception as e:
            print('swap_from_bnb error? %s'%(e))
            return False, 0
        
        return True, hash

    def swap_token_with_target(self, target, balance, draft_bnb_amount, target_multiplier, sell_potion, slippage):
        print("Target profit:  %0.2f x, and will sell %0.0f%% of your holding. current slippage: %0.0f%%"%(target_multiplier, sell_potion * 100, slippage * 100))

        target = Web3.toChecksumAddress(target)
        path = [target, self.bnb]

        amount_in = int(balance * sell_potion)
        buy_bnb_amount = self.bsc.to_wei(draft_bnb_amount)

        
        output = self.__check_sell_vaule(balance, buy_bnb_amount, target_multiplier, path, True, 3)
        if output[2]:
            # sell!
            try:
                amount_min_out = int(output[1]*sell_potion*(1-slippage))
                draft_txn = self.contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(amount_in, 
                                                                                                       amount_min_out,
                                                                                                       path, 
                                                                                                       self.bsc.account, 
                                                                                                       int(self.__deadline()))
                print('Swaping %0.2f BNB for %f token' % (self.bsc.to_bnb(amount_in), self.bsc.to_bnb(amount_min_out)))
                hash = self.bsc.write_contract(draft_txn, self.gwei)
            except Exception as e:
                print('swap_token_with_target error? %s'%(e))
                return False, 0


        return

    def approval_contract(self, target):
        token_contract = self.bsc.load_contract("StandardToken", target)

        output = self.__get_allowance(token_contract, self.contract.address)

        if not(output[0]): return False, 0
        
        if not(output[1] > 0):
            print('token not yet approved for spending, will approve now')
            self.__add_allowance(token_contract)

            
            return self.__get_allowance(token_contract, self.contract.address, True)

        else:
            print('token already approved')

        return True, 1

    def get_balance(self, target, loop = False):
        token_contract = self.bsc.load_contract("StandardToken", target)
        
        output = self.__check_balance(token_contract, loop)

        if output[0]:
            print('%0.8f token available!'%(self.bsc.to_bnb(output[1])))
        else:
            print('no token balance.')

        return output[1]



    def __deadline(self):
        return datetime.timestamp(datetime.now() + timedelta(seconds=1200))

    def __add_allowance(self, contract):
        try:
            draft_txn = contract.functions.approve(self.contract.address, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
            print('Approving...')
            hash = self.bsc.write_contract(draft_txn, self.normal_gwei)

            return True, hash
        except Exception as e:
            print('approve error? %s'%(e))
            return False, 0

        return False, 0




    def __get_allowance(self, contract, router, loop = False):
        txn = contract.functions.allowance(Web3.toChecksumAddress(self.bsc.account), Web3.toChecksumAddress(router))
        err_msg = "NO allowance"
        sleep_interval = 0.3
        compare = lambda x : True

        if loop:  compare = lambda x : x > 0
        
        output = self.__loop_read_contract(txn, err_msg, compare, sleep_interval)

        if output[0]:
            return output

        return False, 0


    def __check_balance(self, contract, loop = False):
        txn = contract.functions.balanceOf(Web3.toChecksumAddress(self.bsc.account))
        err_msg = "No balance yet?"
        sleep_interval = 0.5
        compare = lambda x : True

        if loop:  compare = lambda x : x > 0

        output = self.__loop_read_contract(txn, err_msg, compare, sleep_interval)

        if output[0]:
            return output

        return False, 0

    def __check_sell_vaule(self, amount, buy_bnb_amount, target_multiplier, path, loop = False, sleep_interval = 0.5):
        retry = 0
        sell = False
        while loop:
            try:
                retry += 1
                time.sleep(sleep_interval)
                output = self.__check_amount(amount, path)

                if output[0]:
                    profit = float(output[1] - buy_bnb_amount) * 100 / buy_bnb_amount
                    print("Current profit: %0.2f%% (retry %d)"%(profit, retry), end='\r')
                    if output[1] > int(buy_bnb_amount * target_multiplier):
                        print("target of %0.2f x reached (profit:  %0.2f%%). going to sell!"%(target_multiplier, profit))
                        loop = False
                        sell = True

                if not loop:
                    if output[0]:
                        return True, output[1], sell
                    return False, 0, False
            except Exception as e:
                print("error - @ __check_sell_value Retry %d... [Press Ctrl+C to exit] > %s"%(retry, e), end='\r')


        return False, 0, sell


    

    def __check_amount(self, amount, path):
        txn = self.contract.functions.getAmountsOut(amount,path)
        err_msg = "LP not available?"
        
        output = self.__loop_read_contract(txn, err_msg)

        if output[0]:
            return True, output[1][1]

        return False, 0

    def __always_true(input, req):
        return True

    def __loop_read_contract(self, txn, err_msg, compare = lambda x : True, sleep_interval = 0.1):
        retry = 0
        while retry < 999:
            try:
                time.sleep(sleep_interval)
                output=txn.call()
                if compare(output):
                    return True, output
                else:
                    print("RETRY - %s Retry %d... [Press Ctrl+C to exit]"%(err_msg, retry), end='\r')
                retry += 1
            except KeyboardInterrupt:
                if input("Interrupted.  Input anything to exit, press enter to continue."):
                    retry = 99999999
                    pass

            except Exception as e:
                retry += 1
                print("error - %s Retry %d... [Press Ctrl+C to exit] > %s"%(err_msg, retry, e), end='\r')

                if retry == 999 and not (input("Press enter to retry again...")):
                    retry = 0

        print("error - %s Retry %d... Ended"%(err_msg, retry))

        return False, []


