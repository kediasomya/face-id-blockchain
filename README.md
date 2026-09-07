# Face ID + Blockchain Verification Pipeline

A sophisticated pipeline that detects faces from photos, finds real matching social media posts via reverse-image search, and records tamper-evident verification records on the Ethereum blockchain.

## 🎯 Features

✅ **Face Detection & Encoding** - Detects face-like regions in images and generates a 512-dimensional feature vector (OpenCV) hashed with SHA256  
✅ **Blockchain Verification** - Records face verification data on the **Ethereum Sepolia testnet** as tamper-evident, on-chain records (fully working)  
✅ **End-to-End Pipeline** - Orchestrated CLI tool for complete face-to-blockchain verification  
✅ **Image Search (demo)** - Reverse-image-search step runs with mock data; see [Known Limitations](#-known-limitations)  
✅ **Demo Mode** - Face detection + image search run without any API keys  

### ✅ Live deployment (Sepolia testnet)

| | |
|---|---|
| **Contract** | [`0xA7FeacB5288f2f34979e5DD7A236425b0Bc74c9a`](https://sepolia.etherscan.io/address/0xA7FeacB5288f2f34979e5DD7A236425b0Bc74c9a) |
| **Network** | Ethereum Sepolia (Chain ID `11155111`) |
| **Example TX** | [`0x16570d…4fb06`](https://sepolia.etherscan.io/tx/0x16570d5047025e42b52f62ea11c93de7cefb777c0ff1e0fd02e85db2dbe4fb06) |

## 🔧 Tech Stack

- **Face Processing:** OpenCV (edge detection, multi-scale histogram encoding)
- **Image Search:** Pexels API integration (runs with mock data in demo mode)
- **Blockchain:** Ethereum (Sepolia testnet), Web3.py, Solidity smart contract, py-solc-x
- **Language:** Python 3.9+
- **CLI:** Click framework
- **Testing:** pytest

## 📋 Requirements

- Python 3.9 or higher
- Ethereum account with Sepolia testnet ETH (free via faucet) - *required for real blockchain recording*
- Infura RPC endpoint for Sepolia (free) - *required for real blockchain recording*
- Image search API key (Pexels, free) - *optional; image search runs mocked in demo mode*

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/face-id-blockchain.git
cd face-id-blockchain

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run in Demo Mode (No APIs Required!)

```bash
# Test with demo data
python pipeline.py --image sample_images/test_face.jpg --demo

# Output includes:
# ✓ Detected 1 face
# ✓ Generated face encoding hash
# ✓ Found matching social media post (demo)
# ✓ Recorded on blockchain (demo)
```

### 3. Configure for Real APIs (Optional)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Ethereum - Get a free Infura key from https://infura.io and use the Sepolia endpoint
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

# Use a THROWAWAY test wallet. Get free Sepolia ETH from https://sepoliafaucet.com
ETHEREUM_PRIVATE_KEY=0x...your_private_key...
ETHEREUM_NETWORK=sepolia

# Smart contract address (auto-filled by contract/deploy.py)
CONTRACT_ADDRESS=0x...deployed_contract...

# Optional: image search (runs mocked if left as placeholder)
PEXELS_API_KEY=your_pexels_api_key_here
```

### 4. Deploy Smart Contract (Optional)

```bash
# Set up .env with Sepolia RPC + private key (and fund the wallet) first
python contract/deploy.py

# Output:
# ✓ Contract deployed at: 0x...
# ✓ CONTRACT_ADDRESS updated in .env
# ✓ ABI saved to contract/FaceRegistry_ABI.json
# ✓ View on explorer: https://sepolia.etherscan.io/address/0x...
```

Once deployed, running the pipeline writes a **real transaction** to your
contract on Sepolia — even in `--demo` mode (only the image-search step is mocked).

### 5. Run Full Pipeline

```bash
python pipeline.py --image path/to/image.jpg --output output.json

# Or with debug logging
python pipeline.py --image path/to/image.jpg --debug
```

## 📊 Pipeline Architecture

```
Input Image
    ↓
┌─────────────────────────┐
│  1. Face Detection      │
│  ─────────────────────  │
│  • Load image (OpenCV)  │
│  • Detect face regions  │
│  • Extract embeddings   │
│  • Generate hash        │
└─────────────────────────┘
         ↓ (face_hash, image_path)
┌─────────────────────────┐
│ 2. Image Search         │
│ ─────────────────────── │
│ • Search image API      │
│ • Filter social media   │
│ • Extract metadata      │
│ • Similarity scoring    │
└─────────────────────────┘
    ↓ (post_url, metadata)
┌─────────────────────────┐
│ 3. Blockchain Record    │
│ ─────────────────────── │
│ • Connect to Ethereum   │
│ • Call smart contract   │
│ • Record hash + URL     │
│ • Get TX hash + ID      │
└─────────────────────────┘
         ↓
Output: JSON with full verification record
```

## 📄 Output Format

The pipeline saves results to JSON:

```json
{
  "success": true,
  "steps": {
    "face_detection": {
      "success": true,
      "num_faces": 1,
      "encoding_hash": "cbdf7eab629eca68ae047d493c8e7502",
      "face_locations": [[top, right, bottom, left]],
      "confidences": [0.85],
      "image_shape": [height, width, channels]
    },
    "image_search": {
      "host_url": "https://twitter.com/user/status/...",
      "is_social_media": true,
      "similarity_score": 0.92
    },
    "blockchain": {
      "status": "success",
      "transaction_hash": "0x...",
      "record_id": "0x...",
      "timestamp": 1725674006
    }
  },
  "demo_mode": false
}
```

## 🔒 Security

- **Private Keys:** Never commit `.env` file - kept in gitignore
- **Face Data:** Face embeddings are mathematical vectors, not raw images
- **Hashing:** Face vectors are hashed with SHA256 before blockchain storage
- **API Keys:** All sensitive credentials via environment variables
- **Smart Contract:** Tamper-proof record with event logging

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Image Search (optional — mocked in demo mode)
PEXELS_API_KEY=your_key_here
IMAGE_SEARCH_TIMEOUT=30
MAX_SEARCH_RESULTS=10
SIMILARITY_THRESHOLD=0.85

# Blockchain
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/your_key
ETHEREUM_PRIVATE_KEY=0x...
ETHEREUM_NETWORK=sepolia
CONTRACT_ADDRESS=0x...

# Face Detection
MIN_FACE_SIZE=20
FACE_CONFIDENCE_THRESHOLD=0.6

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/ -v

# Test with debug output
python pipeline.py --image sample_images/test_face.jpg --debug

# Run with demo data
python pipeline.py --image sample_images/test_face.jpg --demo
```

## 📁 Project Structure

```
face-id-blockchain/
├── pipeline.py              # Main CLI entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Configuration template
├── .env                    # Configuration (git-ignored)
├── README.md               # This file
│
├── src/
│   ├── face_detector.py    # OpenCV face detection & encoding
│   ├── image_search.py     # Pexels image search integration (demo/mock in pipeline)
│   ├── blockchain.py       # Ethereum Web3 integration
│   └── utils.py            # Utility functions
│
├── contract/
│   ├── FaceRegistry.sol    # Solidity smart contract
│   ├── deploy.py           # Deployment script
│   └── FaceRegistry_ABI.json # Contract ABI (auto-generated)
│
├── tests/
│   ├── test_face_detector.py
│   ├── test_image_search.py
│   └── test_pipeline.py
│
├── sample_images/
│   └── test_face.jpg       # Test image for demo
│
└── output/
    └── result.json         # Pipeline output
```

## 🔄 How It Works

### Step 1: Face Detection
- Loads image and converts to grayscale
- Applies adaptive histogram equalization
- Detects edges using Canny algorithm
- Finds contours matching face-like proportions
- Generates multi-scale histogram encoding
- Creates SHA256 hash for blockchain storage

### Step 2: Reverse Image Search
- Uses the Pexels API to find candidate images (keyword-based, not true reverse search)
- Extracts metadata (URL, source, confidence)
- Returns best matching result (mocked in the pipeline's demo mode)

### Step 3: Blockchain Recording
- Connects to Ethereum Sepolia testnet via Infura
- Calls the deployed FaceRegistry smart contract (`recordFaceVerification`)
- Records: face hash (bytes32), image URL, post URL, metadata
- Signs and sends a real transaction, waits for confirmation
- Returns transaction hash + record ID (parsed from the emitted event)
- Record is retrievable on-chain via `getRecord(recordId)`

## 📌 Known Limitations

### Face Detection
- **Best for:** Clear, frontal faces in good lighting
- **May fail on:** Very small faces, extreme angles, heavily edited images
- **Note:** Uses edge detection; works on photos, drawings, and artistic renderings

### Image Search
- **⚠️ Not true reverse-image search.** The current `image_search.py` does a Pexels
  *keyword* search (using the filename) and returns stock photos — it does **not**
  identify a person's real social-media post. In the pipeline it runs in demo/mock mode.
- Making this genuine would require a reverse-image/face-search API (e.g. TinEye,
  Google Vision) and a rewrite of the search module. This is the main remaining work item.

### Blockchain (working)
- **Network:** Ethereum Sepolia testnet (Goerli is deprecated/dead)
- **Cost:** a fraction of a testnet ETH per transaction (free from a faucet)
- **Speed:** ~15-120 seconds for confirmation
- **Permanence:** Records are immutable once confirmed and readable back on-chain

### General
- Requires internet connection for image search and blockchain
- Python 3.9+ required (tested on 3.14)
- macOS/Linux/Windows compatible

## 🐛 Troubleshooting

### "No faces detected in image"
- Ensure image has clear, visible face
- Try with `--debug` flag to see detection details
- Test with `sample_images/test_face.jpg`

### "No matching social media post found"
- Image may not be indexed online
- Try with a more popular/widely-shared image
- Check internet connection

### "Blockchain connection failed"
- Verify Infura RPC URL is correct
- Check internet connectivity
- Ensure testnet ETH balance is sufficient
- Use demo mode first: `--demo`

### "Image search API error"
- Verify the Pexels API key in `.env`
- Check the API quota hasn't been exceeded
- Use demo mode for testing: `--demo`

## 🔗 Useful Links

- **Pexels API:** https://www.pexels.com/api/ (free image search key)
- **Infura:** https://infura.io (free RPC endpoints)
- **Sepolia Faucet:** https://sepoliafaucet.com (free testnet ETH)
- **Ethereum Sepolia Explorer:** https://sepolia.etherscan.io
- **Web3.py Documentation:** https://web3py.readthedocs.io

## 📖 API Reference

### CLI Commands

```bash
# Run pipeline with demo data
python pipeline.py --image IMAGE_PATH --demo

# Run with real APIs
python pipeline.py --image IMAGE_PATH --output OUTPUT_FILE

# Run with debug logging
python pipeline.py --image IMAGE_PATH --debug

# Full options
python pipeline.py --help
```

### Python API

```python
from src.face_detector import FaceDetector
from src.image_search import ReverseImageSearcher
from src.blockchain import BlockchainVerifier

# Face detection
detector = FaceDetector()
result = detector.process_image("image.jpg")

# Image search
searcher = ReverseImageSearcher("your_pexels_key")
post = searcher.find_matching_post("image.jpg")

# Blockchain
blockchain = BlockchainVerifier(rpc_url, private_key)
tx = blockchain.record_face_verification(face_hash, image_url, post_url)
```

## 🤝 Contributing

This is a hackathon project! Feel free to:
- Improve face detection accuracy
- Add support for other image search APIs
- Deploy to different blockchains
- Optimize performance

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

Built for Hackathon Challenge: Face ID + Blockchain Verification

---

**Status:** Blockchain recording live on Sepolia ✅ | Face detection working ✅ | Image search is demo/mock ⚠️

**Questions?** Check troubleshooting section above or test with `--demo` mode first!
