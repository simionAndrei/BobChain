import ttk

from pyipv8.ipv8.attestation.trustchain.database import TrustChainDB

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


"""
This script shows a windows that allows the user to inspect all blocks in the blockchain. All tribler_bandwidth
are filtered from the results.
"""


root = tk.Tk()
root.geometry("500x500")
treeview = ttk.Treeview(root, height=28)


def refresh():
    treeview.delete(*treeview.get_children())
    pbhash_to_tree = {}  # Property hash
    for block in persistence2.get_all_blocks():
        if "nightcap" in block.transaction:
            treeview.insert("", "end", text=str(block.transaction).replace('u\'', '').replace('\'', ''))
    for block in persistence.get_all_blocks():
        if block.type != "tribler_bandwidth":
            t = block.transaction
            if "country" in t:
                pbhash_to_tree[block.public_key] = \
                    treeview.insert("", "end", text=str(block.transaction).replace('u\'', '').replace('\'', ''))
                treeview.item(pbhash_to_tree[block.public_key], open=True)
            else:
                treeview.insert(pbhash_to_tree[block.public_key], "end",
                                text=str(block.transaction).replace('u\'', '').replace('\'', ''))


persistence = TrustChainDB('', 'bobchain')
persistence2 = TrustChainDB('', 'bobchainregulations')
button = tk.Button(root,
                   text="Refresh",
                   command=refresh)
button.pack()
scrollbar = tk.Scrollbar(root)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tk.Label(root, text="Blocks:").pack()
treeview.pack(expand=tk.YES, fill=tk.BOTH)
treeview.configure(yscrollcommand=scrollbar.set)
scrollbar.config(command=treeview.yview)
refresh()

root.mainloop()
