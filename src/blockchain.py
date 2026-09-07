"""
Blockchain integration module for Ethereum.
Records face verification data on the Ethereum Sepolia testnet.
"""

import logging
from typing import Dict, Optional
from web3 import Web3
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Default location of the ABI produced by contract/deploy.py
DEFAULT_ABI_PATH = Path(__file__).resolve().parent.parent / "contract" / "FaceRegistry_ABI.json"


class BlockchainVerifier:
    """Handles blockchain record creation and verification."""

    def __init__(self, rpc_url: str, private_key: str, contract_address: str = None,
                 abi_path: str = None):
        """
        Initialize blockchain verifier.

        Args:
            rpc_url: Ethereum RPC endpoint URL
            private_key: Wallet private key (with or without 0x prefix)
            contract_address: Deployed contract address
            abi_path: Path to the contract ABI JSON (defaults to contract/FaceRegistry_ABI.json)
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key if private_key.startswith("0x") else "0x" + private_key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.contract_address = contract_address
        self.contract = None

        if not self.w3.is_connected():
            logger.error("Failed to connect to Ethereum node")
            raise ConnectionError("Cannot connect to Ethereum RPC")

        self.chain_id = self.w3.eth.chain_id
        logger.info(f"Connected to Ethereum (Chain ID: {self.chain_id})")
        logger.info(f"Account: {self.account.address}")

        # Auto-load the deployed contract if we have an address + ABI on disk
        if contract_address and contract_address != "0x0000000000000000000000000000000000000000":
            abi = self._read_abi(abi_path or DEFAULT_ABI_PATH)
            if abi:
                self.load_contract(contract_address, abi)
            else:
                logger.warning(
                    "Contract address provided but ABI not found. "
                    "Run contract/deploy.py to generate FaceRegistry_ABI.json"
                )

    @staticmethod
    def _read_abi(abi_path) -> Optional[list]:
        """Read a contract ABI from a JSON file on disk."""
        path = Path(abi_path)
        if not path.exists():
            logger.warning(f"ABI file not found at {path}")
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read ABI: {str(e)}")
            return None

    def load_contract(self, contract_address: str, contract_abi: list) -> bool:
        """
        Load smart contract instance.

        Args:
            contract_address: Contract deployment address
            contract_abi: Contract ABI (Application Binary Interface)

        Returns:
            True if successfully loaded
        """
        try:
            self.contract_address = Web3.to_checksum_address(contract_address)
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=contract_abi
            )
            logger.info(f"Loaded contract at {self.contract_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to load contract: {str(e)}")
            return False

    @staticmethod
    def _face_hash_to_bytes32(face_hash: str) -> bytes:
        """Convert a hex SHA256 string into a 32-byte value for a bytes32 argument."""
        clean = face_hash[2:] if face_hash.startswith("0x") else face_hash
        raw = bytes.fromhex(clean)
        # Pad/truncate to exactly 32 bytes so it always fits bytes32
        if len(raw) < 32:
            raw = raw.rjust(32, b"\x00")
        return raw[:32]

    def _explorer_url(self, tx_hash: str) -> str:
        """Best-effort block-explorer link for the current network."""
        explorers = {
            1: "https://etherscan.io",
            11155111: "https://sepolia.etherscan.io",
            5: "https://goerli.etherscan.io",
        }
        base = explorers.get(self.chain_id)
        return f"{base}/tx/{tx_hash}" if base else ""

    def record_face_verification(self,
                                 face_hash: str,
                                 image_url: str,
                                 social_post_url: str,
                                 metadata: Dict = None) -> Optional[Dict]:
        """
        Record face verification on the blockchain by calling the FaceRegistry contract.

        Args:
            face_hash: Hex SHA256 hash of the face encoding
            image_url: URL/path of the processed image
            social_post_url: URL of the matching social media post
            metadata: Additional metadata to store (serialized to JSON)

        Returns:
            Dict with transaction hash, record id, and status — or None on failure.
        """
        if not self.contract:
            logger.error(
                "Contract not loaded. Deploy it with contract/deploy.py and set "
                "CONTRACT_ADDRESS in .env"
            )
            return {
                "status": "skipped",
                "reason": "Contract not loaded (missing CONTRACT_ADDRESS / ABI)",
            }

        try:
            metadata_str = json.dumps(metadata or {})
            face_hash_b32 = self._face_hash_to_bytes32(face_hash)

            logger.info("Building recordFaceVerification transaction...")
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            fn = self.contract.functions.recordFaceVerification(
                face_hash_b32,
                image_url,
                social_post_url,
                metadata_str,
            )

            tx = fn.build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": self.chain_id,
            })

            signed = self.account.sign_transaction(tx)
            # web3.py v6 renamed rawTransaction -> raw_transaction; support both
            raw_tx = getattr(signed, "raw_transaction", None) or signed.rawTransaction

            logger.info("Sending transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            tx_hash_hex = tx_hash.hex()
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = "0x" + tx_hash_hex
            logger.info(f"Transaction sent: {tx_hash_hex}")

            logger.info("Waiting for confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            # Pull the record id out of the emitted event
            record_id = None
            try:
                events = self.contract.events.FaceVerificationRecorded().process_receipt(receipt)
                if events:
                    record_id = events[0]["args"]["recordId"].hex()
                    if not record_id.startswith("0x"):
                        record_id = "0x" + record_id
            except Exception as e:
                logger.warning(f"Could not decode event log: {str(e)}")

            status = "success" if receipt.status == 1 else "failed"
            logger.info(f"Transaction {status} in block {receipt.blockNumber}")

            return {
                "status": status,
                "transaction_hash": tx_hash_hex,
                "record_id": record_id,
                "face_hash": face_hash,
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "network": f"chain_{self.chain_id}",
                "explorer_url": self._explorer_url(tx_hash_hex),
                "timestamp": self.w3.eth.get_block(receipt.blockNumber).timestamp,
            }

        except Exception as e:
            logger.error(f"Failed to record verification: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def face_exists(self, face_hash: str) -> bool:
        """Free read call: does this face hash exist in the on-chain registry?"""
        if not self.contract:
            logger.error("Contract not loaded")
            return False
        try:
            return self.contract.functions.verifyFaceExists(
                self._face_hash_to_bytes32(face_hash)
            ).call()
        except Exception as e:
            logger.error(f"face_exists check failed: {str(e)}")
            return False

    def find_record_by_hash(self, face_hash: str) -> Optional[Dict]:
        """
        Scan the registry for a record whose faceHash matches, and return its
        stored data. Read-only (no gas). Returns None if not found.
        """
        if not self.contract:
            logger.error("Contract not loaded")
            return None
        try:
            target = self._face_hash_to_bytes32(face_hash)
            count = self.contract.functions.getRecordCount().call()
            for i in range(count):
                rid = self.contract.functions.getRecordIdAt(i).call()
                rec = self.contract.functions.getRecord(rid).call()
                if bytes(rec[0]) == target:
                    return self._format_record(rid, rec)
            return None
        except Exception as e:
            logger.error(f"find_record_by_hash failed: {str(e)}")
            return None

    def get_record(self, record_id: str) -> Optional[Dict]:
        """Read a single record back from the chain by its record id (hex)."""
        if not self.contract:
            logger.error("Contract not loaded")
            return None
        try:
            clean = record_id[2:] if record_id.startswith("0x") else record_id
            rid = bytes.fromhex(clean)
            rec = self.contract.functions.getRecord(rid).call()
            # An empty/absent record has a zero faceHash
            if bytes(rec[0]) == b"\x00" * 32:
                return None
            return self._format_record(rid, rec)
        except Exception as e:
            logger.error(f"get_record failed: {str(e)}")
            return None

    def _format_record(self, rid: bytes, rec) -> Dict:
        """Turn a raw contract FaceRecord tuple into a readable dict."""
        rid_hex = rid.hex()
        return {
            "record_id": rid_hex if rid_hex.startswith("0x") else "0x" + rid_hex,
            "face_hash": rec[0].hex(),
            "image_url": rec[1],
            "social_post_url": rec[2],
            "timestamp": rec[3],
            "recorded_by": rec[4],
            "metadata": rec[5],
        }

    def get_gas_price(self) -> int:
        """Get current gas price in wei."""
        return self.w3.eth.gas_price

    def get_account_balance(self) -> float:
        """Get account balance in ETH."""
        balance_wei = self.w3.eth.get_balance(self.account.address)
        return float(self.w3.from_wei(balance_wei, "ether"))

    def verify_transaction(self, tx_hash: str) -> Optional[Dict]:
        """
        Verify a transaction on the blockchain.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction receipt summary or None
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                "tx_hash": tx_hash,
                "status": "success" if receipt.status == 1 else "failed",
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "confirmations": self.w3.eth.block_number - receipt.blockNumber
            }
        except Exception as e:
            logger.error(f"Error verifying transaction: {str(e)}")
            return None
