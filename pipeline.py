"""
Main pipeline orchestrator for face ID + blockchain verification.
"""

import click
import logging
import json
from pathlib import Path
from typing import Optional

from src.face_detector import FaceDetector
from src.image_search import ReverseImageSearcher
from src.blockchain import BlockchainVerifier
from src.utils import setup_logging, save_result, load_env_vars, validate_image_path

logger = logging.getLogger(__name__)


class FaceIDPipeline:
    """Orchestrates the complete face ID verification pipeline."""
    
    def __init__(self, env_vars: dict, demo_mode: bool = False):
        """Initialize pipeline with configuration."""
        self.env_vars = env_vars
        self.demo_mode = demo_mode
        self.face_detector = FaceDetector()
        self.image_searcher = None
        self.blockchain = None
        
        # Initialize genuine reverse-image search if a SerpApi key is configured.
        serp_key = env_vars.get("SERPAPI_KEY")
        if serp_key and serp_key != "your_serpapi_key_here":
            self.image_searcher = ReverseImageSearcher(serp_key)
            logger.info("Using SerpApi (Google reverse image search)")
        
        if env_vars.get("ETHEREUM_RPC_URL") and env_vars.get("ETHEREUM_PRIVATE_KEY"):
            if "test-key" not in env_vars.get("ETHEREUM_RPC_URL", "").lower():
                try:
                    self.blockchain = BlockchainVerifier(
                        env_vars["ETHEREUM_RPC_URL"],
                        env_vars["ETHEREUM_PRIVATE_KEY"],
                        env_vars.get("CONTRACT_ADDRESS")
                    )
                except Exception as e:
                    logger.warning(f"Blockchain connection failed: {str(e)}")
    
    def run(self, image_path: str, output_path: str = "output/result.json", demo: bool = False) -> dict:
        """
        Execute the complete pipeline.
        
        Args:
            image_path: Path to input image
            output_path: Path to save result JSON
            demo: Use demo/mock data for demonstration
            
        Returns:
            Pipeline result dictionary
        """
        logger.info("=" * 60)
        logger.info("Starting Face ID + Blockchain Verification Pipeline")
        logger.info("=" * 60)
        
        result = {
            "success": False,
            "steps": {},
            "errors": [],
            "demo_mode": demo
        }
        
        # Step 1: Validate input
        if not validate_image_path(image_path):
            result["errors"].append("Invalid image path")
            return result
        
        # Step 2: Face Detection
        logger.info("\n[STEP 1] Detecting and encoding face...")
        face_result = self.face_detector.process_image(image_path)
        result["steps"]["face_detection"] = face_result
        
        if not face_result.get("success"):
            result["errors"].append(face_result.get("error", "Face detection failed"))
            return result
        
        # Step 3: Reverse Image Search (genuine whenever a searcher is configured)
        logger.info("\n[STEP 2] Reverse image search for a matching web/social post...")

        if self.image_searcher:
            search_result = self.image_searcher.find_matching_post(image_path)
            if not search_result:
                result["errors"].append(
                    "No matching web/social post found via reverse image search"
                )
                return result
            logger.info(f"  Found real match: {search_result['host_url']}")
        elif demo:
            # Offline fallback ONLY — clearly labelled, not for final submission.
            logger.warning("  [OFFLINE DEMO] No SERPAPI_KEY set - using placeholder data")
            logger.warning("  Set SERPAPI_KEY in .env for a genuine search (required by the task)")
            search_result = {
                "image_url": "https://example.com/demo-image.jpg",
                "host_url": "https://twitter.com/demo_user/status/1234567890",
                "is_social_media": True,
                "similarity_score": 0.92,
                "note": "OFFLINE PLACEHOLDER - not a real search result",
            }
        else:
            result["errors"].append(
                "Image search not configured. Set SERPAPI_KEY in .env (or use --demo offline)"
            )
            return result

        result["steps"]["image_search"] = search_result
        
        # Step 4: Blockchain Recording
        logger.info("\n[STEP 3] Recording verification on blockchain...")

        # Prefer a real on-chain record whenever a deployed contract is loaded —
        # even in demo mode, so the demo can still write to Sepolia if configured.
        if self.blockchain and self.blockchain.contract:
            logger.info("  Recording on-chain via FaceRegistry contract...")
            blockchain_result = self.blockchain.record_face_verification(
                face_hash=face_result["encoding_hash"],
                image_url=image_path,
                social_post_url=search_result["host_url"],
                metadata={
                    "num_faces": face_result["num_faces"],
                    "is_social_media": search_result.get("is_social_media"),
                }
            )
            if blockchain_result.get("transaction_hash"):
                logger.info(f"  TX: {blockchain_result['transaction_hash']}")
                if blockchain_result.get("explorer_url"):
                    logger.info(f"  Explorer: {blockchain_result['explorer_url']}")
        elif demo:
            logger.info("  [DEMO MODE] Using mock blockchain record")
            blockchain_result = {
                "status": "success",
                "transaction_hash": "0x" + "a" * 64,
                "record_id": "0x" + "b" * 64,
                "face_hash": face_result["encoding_hash"],
                "timestamp": 1725674006,
                "network": "sepolia_demo"
            }
            logger.info(f"  [DEMO] TX: {blockchain_result['transaction_hash'][:16]}...")
        else:
            logger.warning("Blockchain not available - recording skipped")
            blockchain_result = {
                "status": "skipped",
                "reason": "Blockchain not configured (set ETHEREUM_RPC_URL, "
                          "ETHEREUM_PRIVATE_KEY, CONTRACT_ADDRESS in .env)"
            }

        result["steps"]["blockchain"] = blockchain_result

        # Step 5: Generate a shareable verification certificate (best-effort)
        if blockchain_result.get("record_id") and blockchain_result.get("status") == "success":
            try:
                from src.certificate import generate_certificate
                cert_record = {
                    "face_hash": face_result["encoding_hash"],
                    "record_id": blockchain_result["record_id"],
                    "recorded_by": self.blockchain.account.address if self.blockchain else "",
                    "timestamp": blockchain_result.get("timestamp", ""),
                    "network": blockchain_result.get("network", "Ethereum Sepolia"),
                }
                cert = generate_certificate(
                    cert_record,
                    explorer_url=blockchain_result.get("explorer_url", ""),
                    face_image_path=image_path,
                    output_path="output/certificate.png",
                )
                if cert:
                    result["steps"]["certificate"] = cert
                    logger.info(f"  Certificate: {cert}")
            except Exception as e:
                logger.warning(f"Certificate generation skipped: {e}")

        result["success"] = True
        
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        
        # Save result
        save_result(result, output_path)
        
        return result


@click.command()
@click.option(
    '--image',
    type=click.Path(exists=False),
    required=True,
    help='Path to input image'
)
@click.option(
    '--output',
    type=click.Path(),
    default='output/result.json',
    help='Path to save result JSON'
)
@click.option(
    '--demo',
    is_flag=True,
    help='Run in demo mode with mock data (no APIs required)'
)
@click.option(
    '--debug',
    is_flag=True,
    help='Enable debug logging'
)
def main(image: str, output: str, demo: bool, debug: bool):
    """Face ID + Blockchain Verification Pipeline"""
    
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)
    
    # Load environment variables
    env_vars = load_env_vars()
    
    if not demo and not env_vars.get("SERPAPI_KEY"):
        click.secho("ERROR: SERPAPI_KEY not configured in .env", fg="red")
        click.secho("Get a free key at https://serpapi.com", fg="yellow")
        click.secho("TIP: Use --demo to run offline with placeholder search data", fg="yellow")
        return
    
    # Run pipeline
    pipeline = FaceIDPipeline(env_vars, demo_mode=demo)
    result = pipeline.run(image, output, demo=demo)
    
    # Display results
    if result["success"]:
        click.secho("\n✓ Pipeline succeeded!", fg="green")
        click.echo(f"\nResult saved to: {output}")
        click.echo(f"Faces detected: {result['steps']['face_detection'].get('num_faces', 0)}")
        click.echo(f"Social post match: {result['steps']['image_search'].get('host_url', 'N/A')}")
        
        if "blockchain" in result["steps"]:
            bc = result["steps"]["blockchain"]
            tx = bc.get("transaction_hash")
            if tx:
                click.echo(f"Blockchain TX: {tx}")
                if bc.get("record_id"):
                    click.echo(f"Record ID: {bc['record_id']}")
                if bc.get("explorer_url"):
                    click.echo(f"Explorer: {bc['explorer_url']}")
            else:
                click.echo(f"Blockchain: {bc.get('status', 'N/A')} "
                           f"({bc.get('reason', bc.get('error', ''))})")
        
        if result.get("demo_mode"):
            click.secho("\n[DEMO MODE] Using mock data for demonstration", fg="cyan")
    else:
        click.secho("\n✗ Pipeline failed!", fg="red")
        for error in result.get("errors", []):
            click.echo(f"  - {error}")


if __name__ == "__main__":
    main()
