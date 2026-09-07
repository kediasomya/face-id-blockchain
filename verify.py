"""
Re-verification CLI.

Demonstrates re-verifying data against the on-chain record — the tamper-evident
half of the pipeline. Three modes:

  1. --record-id 0x...   read a record straight back from the chain
  2. --tx 0x...          confirm a transaction was mined successfully
  3. --image path.jpg    re-hash a face image and check it against the registry
                         (proves tamper detection: edited image -> no match)
"""

import click
import logging

from src.face_detector import FaceDetector
from src.blockchain import BlockchainVerifier
from src.utils import setup_logging, load_env_vars

logger = logging.getLogger(__name__)


def _connect(env_vars: dict) -> BlockchainVerifier:
    """Build a BlockchainVerifier from .env, or exit with a helpful message."""
    rpc = env_vars.get("ETHEREUM_RPC_URL")
    pk = env_vars.get("ETHEREUM_PRIVATE_KEY")
    addr = env_vars.get("CONTRACT_ADDRESS")
    if not (rpc and pk):
        raise click.ClickException("Set ETHEREUM_RPC_URL and ETHEREUM_PRIVATE_KEY in .env")
    verifier = BlockchainVerifier(rpc, pk, addr)
    if not verifier.contract:
        raise click.ClickException(
            "Contract not loaded. Set CONTRACT_ADDRESS in .env and deploy with "
            "contract/deploy.py"
        )
    return verifier


def _print_record(rec: dict):
    click.secho("\n  VERIFIED ON-CHAIN", fg="green", bold=True)
    click.echo(f"  Record ID     : {rec['record_id']}")
    click.echo(f"  Face hash     : {rec['face_hash']}")
    click.echo(f"  Image URL     : {rec['image_url']}")
    click.echo(f"  Social post   : {rec['social_post_url']}")
    click.echo(f"  Recorded by   : {rec['recorded_by']}")
    click.echo(f"  Timestamp     : {rec['timestamp']}")
    click.echo(f"  Metadata      : {rec['metadata']}")


@click.command()
@click.option('--record-id', help='Record ID (0x...) to read back from the chain')
@click.option('--tx', help='Transaction hash (0x...) to confirm')
@click.option('--image', type=click.Path(exists=True), help='Image to re-hash and check against the registry')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(record_id, tx, image, debug):
    """Re-verify data against the on-chain FaceRegistry record."""
    setup_logging("DEBUG" if debug else "INFO")
    env_vars = load_env_vars()

    if not any([record_id, tx, image]):
        raise click.ClickException("Provide one of --record-id, --tx, or --image")

    verifier = _connect(env_vars)
    click.echo(f"\nContract: {verifier.contract_address}  (chain {verifier.chain_id})")

    # Mode 1: read a record back by ID
    if record_id:
        rec = verifier.get_record(record_id)
        if rec:
            _print_record(rec)
        else:
            click.secho(f"\n  No record found for {record_id}", fg="red")

    # Mode 2: confirm a transaction
    if tx:
        info = verifier.verify_transaction(tx)
        if info and info["status"] == "success":
            click.secho(f"\n  TX CONFIRMED - block {info['block_number']}, "
                        f"{info['confirmations']} confirmations", fg="green", bold=True)
            click.echo(f"  {verifier._explorer_url(tx)}")
        else:
            click.secho(f"\n  TX not confirmed / not found: {tx}", fg="red")

    # Mode 3: re-hash an image and check tamper-evidence
    if image:
        click.echo(f"\nRe-hashing face from: {image}")
        face = FaceDetector().process_image(image)
        if not face.get("success"):
            raise click.ClickException(f"Face detection failed: {face.get('error')}")
        face_hash = face["encoding_hash"]
        click.echo(f"Computed face hash: {face_hash}")

        rec = verifier.find_record_by_hash(face_hash)
        if rec:
            click.secho("\n  ✅ MATCH - this exact face is registered on-chain (authentic)",
                        fg="green", bold=True)
            _print_record(rec)
        else:
            click.secho("\n  ❌ TAMPER DETECTED - this face hash is NOT on the registry.",
                        fg="red", bold=True)
            click.secho("     The image does not match any recorded identity "
                        "(edited / different / unregistered).", fg="red")


if __name__ == "__main__":
    main()
