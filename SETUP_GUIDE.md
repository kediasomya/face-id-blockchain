# Complete Setup Guide - Face ID + Blockchain Pipeline

This guide walks through setting up the project for real-world usage with actual APIs.

## Table of Contents
1. [Basic Setup](#basic-setup)
2. [Bing Image Search API Setup](#bing-image-search-api-setup)
3. [Ethereum Goerli Testnet Setup](#ethereum-goerli-testnet-setup)
4. [Smart Contract Deployment](#smart-contract-deployment)
5. [Running with Real APIs](#running-with-real-apis)
6. [Troubleshooting](#troubleshooting)

---

## Basic Setup

### Prerequisites
- Python 3.9+
- Git
- Text editor or IDE

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/face-id-blockchain.git
cd face-id-blockchain
```

### Step 2: Create Virtual Environment

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Verify installation:
```bash
python pipeline.py --help
```

---

## Bing Image Search API Setup

### Why Bing Image Search?
- Free tier: 1000 queries/month (sufficient for hackathon/demo)
- Good accuracy for finding social media posts
- Simple integration with standard HTTP requests

### Step 1: Get Bing API Key

1. Go to [Azure Portal](https://portal.azure.com/)
2. Click "Create a resource"
3. Search for "Bing Search v7"
4. Click "Create"
5. Fill in form:
   - **Name:** `face-id-search` (any name)
   - **Pricing tier:** Free (F0)
6. Click "Create"
7. Go to "Resource Management" → "Keys and Endpoint"
8. Copy **Key 1** (this is your API key)

### Step 2: Configure .env

```bash
cp .env.example .env
```

Edit `.env`:
```env
BING_SEARCH_KEY=your_key_from_step_1
```

### Step 3: Test Bing Search

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
from src.image_search import ReverseImageSearcher

load_dotenv()
api_key = os.getenv('BING_SEARCH_KEY')

searcher = ReverseImageSearcher(api_key)
# This will actually search - use with caution on quota
print("✓ Bing Search API configured successfully!")
EOF
```

---

## Ethereum Goerli Testnet Setup

### Why Goerli Testnet?
- Official Ethereum test network
- Free testnet ETH available via faucets
- Stable and widely supported
- Can be used for free to test smart contracts

### Step 1: Create Ethereum Account

#### Option A: Using MetaMask (Easy)
1. Install [MetaMask browser extension](https://metamask.io)
2. Create new wallet
3. Switch to "Goerli Test Network" (top-left dropdown)
4. Copy your account address (shown in MetaMask)

#### Option B: Using Command Line
```bash
python3 << 'EOF'
from eth_account import Account

# Generate new account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
EOF
```

### Step 2: Get Goerli Testnet ETH

Visit one of these faucets and paste your address:
- [Goerli Faucet](https://goerlifaucet.com) - Requires GitHub/Twitter
- [Alchemy Faucet](https://www.alchemy.com/faucets/goerli)

**You'll receive ~0.1 ETH (free, takes 1-2 minutes)**

### Step 3: Get Infura RPC Endpoint

1. Go to [Infura](https://infura.io)
2. Sign up (free)
3. Create new project
4. Copy the Goerli testnet endpoint (looks like: `https://goerli.infura.io/v3/YOUR_KEY`)

### Step 4: Configure .env

Edit `.env`:
```env
ETHEREUM_RPC_URL=https://goerli.infura.io/v3/YOUR_INFURA_KEY
ETHEREUM_PRIVATE_KEY=0x... (your private key from Step 1)
ETHEREUM_NETWORK=goerli
```

### Step 5: Verify Setup

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
from src.blockchain import BlockchainVerifier

load_dotenv()
rpc = os.getenv('ETHEREUM_RPC_URL')
private_key = os.getenv('ETHEREUM_PRIVATE_KEY')

try:
    blockchain = BlockchainVerifier(rpc, private_key)
    balance = blockchain.get_account_balance()
    print(f"✓ Connected to Ethereum!")
    print(f"  Account: {blockchain.account.address}")
    print(f"  Balance: {balance} ETH")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

---

## Smart Contract Deployment

### Prerequisites
- Ethereum Goerli account with ETH (from previous section)
- `.env` configured with RPC URL and private key

### Step 1: Check Account Balance

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
rpc = os.getenv('ETHEREUM_RPC_URL')
private_key = os.getenv('ETHEREUM_PRIVATE_KEY')

w3 = Web3(Web3.HTTPProvider(rpc))
account = w3.eth.account.from_key(private_key)
balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')

print(f"Account: {account.address}")
print(f"Balance: {balance} ETH")

if balance < 0.01:
    print("\n⚠️  Low balance! Get testnet ETH from:")
    print("   https://goerlifaucet.com")
else:
    print("✓ Sufficient balance to deploy contract")
EOF
```

### Step 2: Deploy Smart Contract

```bash
# Install solc if needed
pip install py-solc-x

# Deploy
python contract/deploy.py
```

Expected output:
```
✓ Contract deployed at: 0x...
✓ CONTRACT_ADDRESS updated in .env
```

### Step 3: Verify Deployment

```bash
# Check transaction on Goerli Etherscan
echo $CONTRACT_ADDRESS  # Copy this address
# Go to https://goerli.etherscan.io/address/0x...
```

---

## Running with Real APIs

### Demo Mode (No APIs)
```bash
python pipeline.py --image sample_images/test_face.jpg --demo
```

### Real Mode (All APIs)
```bash
# Make sure .env is configured with all keys
python pipeline.py --image path/to/image.jpg --output result.json
```

### With Debug Output
```bash
python pipeline.py --image path/to/image.jpg --debug
```

---

## Expected Output

When running successfully, you'll see:

```
============================================================
Starting Face ID + Blockchain Verification Pipeline
============================================================

[STEP 1] Detecting and encoding face...
✓ Loaded image
✓ Detected 1 face(s)

[STEP 2] Searching for matching social media posts...
✓ Found match: https://twitter.com/user/status/...

[STEP 3] Recording verification on blockchain...
✓ Transaction sent

============================================================
Pipeline completed successfully!
============================================================

✓ Pipeline succeeded!
  Result saved to: result.json
  Faces detected: 1
  Social post match: https://twitter.com/user/status/...
  Blockchain TX: 0xabc123...
```

---

## Troubleshooting

### "Bing Search API error 401"
**Problem:** Invalid API key
**Solution:**
1. Verify key is correct in `.env`
2. Check key hasn't expired
3. Verify it's from Bing Search (not other service)

### "Cannot connect to Ethereum node"
**Problem:** Invalid RPC URL or network issue
**Solution:**
1. Verify RPC URL format: `https://goerli.infura.io/v3/YOUR_KEY`
2. Check internet connection
3. Try in demo mode first: `--demo`

### "Insufficient funds to deploy contract"
**Problem:** Account balance < 0.01 ETH
**Solution:**
1. Get more testnet ETH from faucet
2. Wait 1-2 minutes for transaction to confirm
3. Check balance: `python3 -c "from web3 import Web3; ..."`

### "No faces detected"
**Problem:** Image quality or detection settings
**Solution:**
1. Test with `sample_images/test_face.jpg` first
2. Ensure face is clearly visible
3. Try different image with better lighting
4. Use `--debug` flag to see detection details

### "ModuleNotFoundError"
**Problem:** Dependencies not installed
**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Contract deployment fails"
**Problem:** Gas limit or nonce issues
**Solution:**
1. Increase timeout in `contract/deploy.py`
2. Wait for pending transactions to clear
3. Try again in a few minutes

---

## Cost Analysis

### Bing Image Search API
- **Free tier:** 1000 queries/month
- **Per query:** $0 (free tier)
- **Sufficient for:** Hackathon + development

### Ethereum Goerli Testnet
- **Contract deployment:** ~$0 (using free testnet ETH)
- **Face verification record:** ~$0 (testnet)
- **Production cost (mainnet):** ~$0.50 per record (highly variable)

### Total Setup Cost
- **Free tier:** $0 ✓
- **Paid tier:** ~$10-20/month (optional)

---

## Next Steps

1. **Test locally:** Run with `--demo` mode
2. **Get free API keys:** Follow sections above
3. **Deploy smart contract:** Run `python contract/deploy.py`
4. **Run real pipeline:** `python pipeline.py --image image.jpg`
5. **Record demo video:** Capture full end-to-end run

---

## Additional Resources

### Bing Search API
- [Documentation](https://docs.microsoft.com/en-us/bing/search-apis/bing-image-search/overview)
- [Pricing](https://www.microsoft.com/en-us/bing/apis/pricing)

### Ethereum & Web3
- [Web3.py Documentation](https://web3py.readthedocs.io)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Goerli Testnet Info](https://goerli.net/)

### Infura
- [Infura Dashboard](https://infura.io)
- [Infura Docs](https://docs.infura.io/)

### Testing Tools
- [Goerli Etherscan](https://goerli.etherscan.io)
- [Remix IDE](https://remix.ethereum.org) (for contract testing)

---

## Need Help?

1. Check the [README.md](README.md) main documentation
2. Review this setup guide
3. Use `--debug` flag for detailed logs
4. Test with `--demo` mode first
5. Check troubleshooting section above

Good luck! 🚀
