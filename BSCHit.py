from web3 import Web3
import Bsc, PancakeRouter


address="" # your BEP20 address
private_key="" # your wallet private key


bsc = Bsc.Bsc(address, private_key)
# 30 gwei for trading
pcs = PancakeRouter.PancakeRouter(bsc, 30)
bnb_amount = 0
while bnb_amount <=0:
    try:
        bnb = input('Enter BNB amount to trade:  ')
        bnb_amount = float(bnb)
    except:
        bnb = 0
print("going to trade %f BNB"%(bnb_amount))

input_target = True

while input_target:
    try:
        target = input('Enter token address:  ')
        Web3.toChecksumAddress(target)
        input_target = False
    except:
        True
print("---------------INITIALISED----------------")
output = pcs.get_balance(target, False)
swap = True
if output > 0 and input("You have balance on hand, swap anyway? Press enter to swap, input to skip swap"):
    swap = False

    
print("---------------SWAPPING----------------")
if swap:
    ##   slippage, Fair Launch (ignore slippage)
    pcs.swap_from_bnb(bnb_amount, target, 0.4, True)
else:
    print("swap skipped")

target_amount = pcs.get_balance(target, True)


print("---------------APPROVAL----------------")
output = pcs.approval_contract(target)
print("---------------TO SELL----------------")
##   multiplier, potion to sell, slippage
pcs.swap_token_with_target(target, target_amount, bnb_amount, 2, 1, 0.3)

