# BOBChain: Booked on Blockchain

BOBChain is a blockchain solution that strives totackle  the  issue  of  overbooking  and  government  regulations.This  is  achieved  by  allowing  Online  Travel  Agencies(OTAs)  tocheck whether an accommodation has been previously bookedby  another  OTA  or  if  the  accommodation  has  exceeded  itslegal  nightcap  limit  set  by  a  municipality/government.

<img src="https://github.com/simionAndrei/BobChain/blob/master/images/bob_simple.jpg" width="350" height="200" />

## BOBChain Features

**BOBChain** offers a blockchain solution to tackle the problem of legal nightcap limits that will allow current and future OTA to communicate on a decentralized ledger to ensure that no legal limits are exceeded.

**BOBChain** offers a blockchain solution to tackle the dreaded overbooking, currently there is no central platform to check if an accommodation that is put up for rent on multiple OTA sites is double booked. The overbooking issue costs the OTAs money as an overbooking means they must usually refund or find a new accommodation for the booking customer.

**BOBChain** offers a blockchain solution with authorized homeowner licenses from municipalities, these licenses can be shared by the homer-owner to different OTAs. The OTAs with these licenses can ensure no overbookings take place or nightcap limits are exceeded.

**BOBChain** offers a blockchain solution that is decentralized and anonymous between the bookings of different OTA parties. Ensuring the privacy between different OTAs. Meaning no valuable business information is exchanged between OTAs.

![alt text](https://github.com/simionAndrei/BobChain/blob/master/images/arch.png "Stakeholder Architecture BOBChain")


## Architecture of BOBChain

BOBChain is a direct extension of Triblers *TrustChainCommunity*; with some modifications to the validation of transactions and communications with other TrustChainCommunities. BOBChain's artitecture is centered around the idea that every homeowner gets a license and this license is seen as an accommodations private *TrustChain* or in this case a *BOBChain*. A design choice was made to have the municipality and OTAs run the TrustChainCommunities for the home-owners. Allowing *BOBChain* not to depend on homeowners keeping the service running but the municipality and OTAs.

![alt text](https://github.com/simionAndrei/BobChain/blob/master/images/BobChain.jpg "How we used TrustChain for this problem")

### **Overview BOBChain Stakeholder Interaction**

![alt text](https://github.com/simionAndrei/BobChain/blob/master/images/arch.png "Stakeholder Architecture BOBChain")

---

## **How to make use of BOBChain**

To run the BOBChain as of ```18/02/2019 on ubuntu 18.04```
The following steps will need to be done:

Clone this repository with git with the following command:

```bash
git clone https://github.com/simionAndrei/BobChain.git pyipv8
```

Install the required dependencies for IPv8, these can be found in the ```requirements.txt``` file.

```bash
pip install --upgrade -r requirements.txt
```

Make sure that ```tkinter``` for python is installed:

```bash
sudo apt-get install python-tk
```

Copy main.py and simulator.py to the parent directory of `pyipv8`:

```bash
cp main.py ../
cp simulator.py ../
```

To get the GUI started and the IPv8 overlay ```python version 2``` must be used:

```bash
python2 main.py
```

This should launch the GUI interface an all interactions with the BOBChain can be done from there

---

## Further details

For the full bussiness details of our project, please refer to the scientific report: [BOBChain - Booked on Blockchain](https://drive.google.com/file/d/1J48HlOTgRf-W9jzj4tfXTmbBp4NzERXH/view?usp=sharing)

