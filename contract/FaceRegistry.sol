// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FaceRegistry
 * @dev Records face verification data on blockchain
 */
contract FaceRegistry {
    
    struct FaceRecord {
        bytes32 faceHash;
        string imageUrl;
        string socialPostUrl;
        uint256 timestamp;
        address recordedBy;
        string metadata;
    }
    
    // Mapping of record ID to face record
    mapping(bytes32 => FaceRecord) public records;
    
    // Array of all record IDs for enumeration
    bytes32[] public recordIds;
    
    // Event emitted when a new verification is recorded
    event FaceVerificationRecorded(
        bytes32 indexed recordId,
        bytes32 indexed faceHash,
        address indexed recordedBy,
        uint256 timestamp
    );
    
    /**
     * @dev Record a face verification on the blockchain
     * @param faceHash Hash of the face encoding
     * @param imageUrl URL of the original image
     * @param socialPostUrl URL of the matching social media post
     * @param metadata Additional metadata as JSON string
     */
    function recordFaceVerification(
        bytes32 faceHash,
        string memory imageUrl,
        string memory socialPostUrl,
        string memory metadata
    ) public returns (bytes32 recordId) {
        
        // Generate unique record ID
        recordId = keccak256(abi.encodePacked(
            faceHash,
            msg.sender,
            block.timestamp,
            recordIds.length
        ));
        
        // Create face record
        records[recordId] = FaceRecord({
            faceHash: faceHash,
            imageUrl: imageUrl,
            socialPostUrl: socialPostUrl,
            timestamp: block.timestamp,
            recordedBy: msg.sender,
            metadata: metadata
        });
        
        // Add to record IDs array
        recordIds.push(recordId);
        
        // Emit event
        emit FaceVerificationRecorded(recordId, faceHash, msg.sender, block.timestamp);
        
        return recordId;
    }
    
    /**
     * @dev Get a face verification record
     * @param recordId ID of the record to retrieve
     */
    function getRecord(bytes32 recordId) public view returns (FaceRecord memory) {
        return records[recordId];
    }
    
    /**
     * @dev Get total number of records
     */
    function getRecordCount() public view returns (uint256) {
        return recordIds.length;
    }
    
    /**
     * @dev Get record ID at specific index
     * @param index Index in the records array
     */
    function getRecordIdAt(uint256 index) public view returns (bytes32) {
        require(index < recordIds.length, "Index out of bounds");
        return recordIds[index];
    }
    
    /**
     * @dev Verify that a face hash exists in the registry
     * @param faceHash Hash to verify
     */
    function verifyFaceExists(bytes32 faceHash) public view returns (bool) {
        for (uint256 i = 0; i < recordIds.length; i++) {
            if (records[recordIds[i]].faceHash == faceHash) {
                return true;
            }
        }
        return false;
    }
}
