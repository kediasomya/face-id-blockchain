"""
Blockchain integration module for Ethereum.
Records face verification data on Ethereum Goerli testnet.
"""

import logging
from typing import Dict, Optional
from web3 import Web3
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BlockchainVerifier:
    """Handles blockchain record creation and verification."""
    
    def __init__(self, rpc_url: str, private_key: str, contract_address: str = None):
        """
        Initialize blockchain verifier.
        
        Args:
            rpc_url: Ethereum RPC endpoint URL
            private_key: Wallet private key (without 0x prefix)
            contract_address: Deployed contract address
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key if private_key.startswith("0x") else "0x" + private_key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.contract_address = contract_address
        self.contract = None
        
        if not self.w3.is_connected():
            logger.error("Failed to connect to Ethereum node")
            raise ConnectionError("Cannot connect to Ethereum RPC")
        
        logger.info(f"Connected to Ethereum (Chain ID: {self.w3.eth.chain_id})")
        logger.info(f"Account: {self.account.address}")
    
    def load_contract(self, contract_address: str, contract_abi: Dict) -> bool:
        """
        Load smart contract instance.
        
        Args:
            contract_address: Contract deployment address
            contract_abi: Contract ABI (Application Binary Interface)
            
        Returns:
            True if successfully loaded
        """
        try:
            self.contract_address = contract_address
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=contract_abi
            )
            logger.info(f"Loaded contract at {contract_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to load contract: {str(e)}")
            return False
    
    def record_face_verification(self, 
                                face_hash: str, 
                                image_url: str,
                                social_post_url: str,
                                metadata: Dict = None) -> Optional[Dict]:
        """
        Record face verification on blockchain.
        
        Args:
            face_hash: Hash of face encoding
            image_url: URL of processed image
            social_post_url: URL of matching social media post
            metadata: Additional metadata to store
            
        Returns:
            Transaction receipt or None on failure
        """
        if not self.contract:
            logger.error("Contract not loaded. Call load_contract() first")
            return None
        
        try:
            # Build metadata string
            metadata_str = json.dumps(metadata or {})
            
            # Create transaction
            # Note: This assumes contract has recordFaceVerification function
            # Adjust based on actual contract interface
            
            logger.info("Preparing blockchain transaction...")
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Build transaction (example - adjust to match contract)
            # Assuming contract function: recordFaceVerification(bytes32 faceHash, string imageUrl, string postUrl, string metadata)
            
            # For demo, just simulate the recording
            tx_dict = {
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
                "from": self.account.address,
                "chainId": self.w3.eth.chain_id
            }
            
            logger.info("Transaction prepared (awaiting actual contract deployment)")
            
            return {
                "status": "pending",
                "transaction": tx_dict,
                "face_hash": face_hash,
                "timestamp": self.w3.eth.get_block("latest").timestamp
            }
        
        except Exception as e:
            logger.error(f"Failed to record verification: {str(e)}")
            return None
    
    def get_gas_price(self) -> int:
        """Get current gas price in wei."""
        return self.w3.eth.gas_price
    
    def get_account_balance(self) -> float:
        """Get account balance in ETH."""
        balance_wei = self.w3.eth.get_balance(self.account.address)
        return self.w3.from_wei(balance_wei, "ether")
    
    def verify_transaction(self, tx_hash: str) -> Optional[Dict]:
        """
        Verify a transaction on blockchain.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt or None
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
