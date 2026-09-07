"""
Smart contract deployment script for FaceRegistry contract.
Deploys to Ethereum Goerli testnet via Infura.
"""

import json
import logging
from pathlib import Path
from web3 import Web3
from solcx import compile_source
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

def load_contract_source(contract_path: str) -> str:
    """Load Solidity contract source code."""
    with open(contract_path, 'r') as f:
        return f.read()


def compile_contract(source_code: str) -> dict:
    """Compile Solidity contract using solc."""
    try:
        compiled = compile_source(
            source_code,
            output_values=['abi', 'bin'],
            solc_version='0.8.0'
        )
        logger.info("Contract compiled successfully")
        return compiled
    except Exception as e:
        logger.error(f"Compilation failed: {str(e)}")
        raise


def deploy_contract(w3: Web3, contract_info: dict, account) -> str:
    """Deploy compiled contract to blockchain."""
    try:
        contract_source = list(contract_info.values())[0]
        contract_abi = contract_source['abi']
        contract_bytecode = contract_source['bin']
        
        # Create contract factory
        contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build and sign transaction
        tx = contract.constructor().build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 5000000,
            'gasPrice': gas_price,
        })
        
        signed_tx = account.sign_transaction(tx)
        
        # Send transaction
        logger.info("Sending deployment transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Transaction hash: {tx_hash.hex()}")
        
        # Wait for receipt
        logger.info("Waiting for contract deployment...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        contract_address = receipt.contractAddress
        logger.info(f"Contract deployed at: {contract_address}")
        
        return contract_address
    
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise


def save_deployment_info(contract_address: str, contract_abi: list, output_file: str = ".env"):
    """Save deployment info to .env file."""
    try:
        # Read existing .env
        env_content = ""
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                env_content = f.read()
        
        # Update or add CONTRACT_ADDRESS
        if "CONTRACT_ADDRESS=" in env_content:
            lines = env_content.split('\n')
            lines = [line for line in lines if not line.startswith('CONTRACT_ADDRESS=')]
            env_content = '\n'.join(lines)
        
        # Add contract address
        env_content += f"\nCONTRACT_ADDRESS={contract_address}\n"
        
        with open(output_file, 'w') as f:
            f.write(env_content)
        
        # Also save ABI
        abi_file = Path("contract/FaceRegistry_ABI.json")
        with open(abi_file, 'w') as f:
            json.dump(contract_abi, f, indent=2)
        
        logger.info(f"Deployment info saved to {output_file}")
    
    except Exception as e:
        logger.error(f"Failed to save deployment info: {str(e)}")


def main():
    """Main deployment script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Get configuration
    rpc_url = os.getenv("ETHEREUM_RPC_URL")
    private_key = os.getenv("ETHEREUM_PRIVATE_KEY")
    
    if not rpc_url or not private_key:
        logger.error("Missing ETHEREUM_RPC_URL or ETHEREUM_PRIVATE_KEY in .env")
        return False
    
    # Connect to Ethereum
    logger.info("Connecting to Ethereum...")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        logger.error("Failed to connect to Ethereum node")
        return False
    
    logger.info(f"Connected to network (Chain ID: {w3.eth.chain_id})")
    
    # Setup account
    account = w3.eth.account.from_key(private_key)
    balance = w3.from_wei(w3.eth.get_balance(account.address), "ether")
    logger.info(f"Account: {account.address}")
    logger.info(f"Balance: {balance} ETH")
    
    if balance < 0.01:
        logger.warning("Low balance! Get testnet ETH from faucet: https://goerlifaucet.com")
    
    # Load and compile contract
    logger.info("Loading contract source...")
    contract_path = Path("contract/FaceRegistry.sol")
    
    if not contract_path.exists():
        logger.error(f"Contract file not found: {contract_path}")
        return False
    
    source_code = load_contract_source(str(contract_path))
    compiled = compile_contract(source_code)
    
    # Deploy contract
    logger.info("Deploying contract...")
    contract_address = deploy_contract(w3, compiled, account)
    
    # Save deployment info
    contract_info = list(compiled.values())[0]
    save_deployment_info(contract_address, contract_info['abi'])
    
    logger.info("\n" + "="*60)
    logger.info("Deployment successful!")
    logger.info(f"Contract Address: {contract_address}")
    logger.info(f"Network: Goerli Testnet (Chain ID: {w3.eth.chain_id})")
    logger.info("="*60)
    
    return True


if __name__ == "__main__":
    main()
