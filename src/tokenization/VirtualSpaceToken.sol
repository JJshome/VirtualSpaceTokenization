// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title VirtualSpaceToken
 * @dev Contract for tokenizing virtual spaces as NFTs
 */
contract VirtualSpaceToken is ERC721URIStorage, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    using SafeMath for uint256;
    
    // Token ID counter
    Counters.Counter private _tokenIds;
    
    // Virtual space metadata structure
    struct VirtualSpace {
        string name;
        string description;
        uint256 width;
        uint256 height;
        uint256 depth;
        string theme;
        string[] features;
        uint256 createdAt;
        bool verified;
    }
    
    // Mapping from token ID to virtual space
    mapping(uint256 => VirtualSpace) public virtualSpaces;
    
    // Mapping for space verification
    mapping(uint256 => bool) public verifiedSpaces;
    
    // Value assessment authority
    address public assessmentAuthority;
    
    // Maximum space dimensions
    uint256 public constant MAX_DIMENSION = 10000;
    
    // Events
    event SpaceTokenized(uint256 indexed tokenId, address indexed owner, string name);
    event SpaceVerified(uint256 indexed tokenId, bool verified);
    event AssessmentAuthorityUpdated(address indexed previousAuthority, address indexed newAuthority);
    
    /**
     * @dev Constructor
     */
    constructor() ERC721("VirtualSpaceToken", "VST") {
        assessmentAuthority = msg.sender;
    }
    
    /**
     * @dev Set the assessment authority address
     * @param _authority The new assessment authority address
     */
    function setAssessmentAuthority(address _authority) external onlyOwner {
        require(_authority != address(0), "Invalid address");
        emit AssessmentAuthorityUpdated(assessmentAuthority, _authority);
        assessmentAuthority = _authority;
    }
    
    /**
     * @dev Tokenize a virtual space
     * @param _to The owner of the token
     * @param _name Name of the virtual space
     * @param _description Description of the virtual space
     * @param _width Width of the virtual space
     * @param _height Height of the virtual space
     * @param _depth Depth of the virtual space
     * @param _theme Theme of the virtual space
     * @param _features Array of features in the virtual space
     * @param _tokenURI URI containing token metadata
     * @return The new token ID
     */
    function tokenizeSpace(
        address _to,
        string memory _name,
        string memory _description,
        uint256 _width,
        uint256 _height,
        uint256 _depth,
        string memory _theme,
        string[] memory _features,
        string memory _tokenURI
    ) 
        external
        nonReentrant
        returns (uint256)
    {
        require(_to != address(0), "Invalid address");
        require(_width > 0 && _width <= MAX_DIMENSION, "Invalid width");
        require(_height > 0 && _height <= MAX_DIMENSION, "Invalid height");
        require(_depth > 0 && _depth <= MAX_DIMENSION, "Invalid depth");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();
        
        _mint(_to, newTokenId);
        _setTokenURI(newTokenId, _tokenURI);
        
        virtualSpaces[newTokenId] = VirtualSpace({
            name: _name,
            description: _description,
            width: _width,
            height: _height,
            depth: _depth,
            theme: _theme,
            features: _features,
            createdAt: block.timestamp,
            verified: false
        });
        
        emit SpaceTokenized(newTokenId, _to, _name);
        
        return newTokenId;
    }
    
    /**
     * @dev Verify a virtual space
     * @param _tokenId The ID of the token to verify
     * @param _verified The verification status
     */
    function verifySpace(uint256 _tokenId, bool _verified) external {
        require(_exists(_tokenId), "Token does not exist");
        require(msg.sender == assessmentAuthority || msg.sender == owner(), "Not authorized");
        
        virtualSpaces[_tokenId].verified = _verified;
        verifiedSpaces[_tokenId] = _verified;
        
        emit SpaceVerified(_tokenId, _verified);
    }
    
    /**
     * @dev Get virtual space details
     * @param _tokenId The ID of the token
     * @return The virtual space details
     */
    function getVirtualSpace(uint256 _tokenId) external view returns (VirtualSpace memory) {
        require(_exists(_tokenId), "Token does not exist");
        return virtualSpaces[_tokenId];
    }
    
    /**
     * @dev Get the features of a virtual space
     * @param _tokenId The ID of the token
     * @return The features of the virtual space
     */
    function getSpaceFeatures(uint256 _tokenId) external view returns (string[] memory) {
        require(_exists(_tokenId), "Token does not exist");
        return virtualSpaces[_tokenId].features;
    }
    
    /**
     * @dev Get the dimensions of a virtual space
     * @param _tokenId The ID of the token
     * @return width The width of the virtual space
     * @return height The height of the virtual space
     * @return depth The depth of the virtual space
     */
    function getSpaceDimensions(uint256 _tokenId) external view returns (uint256 width, uint256 height, uint256 depth) {
        require(_exists(_tokenId), "Token does not exist");
        VirtualSpace memory space = virtualSpaces[_tokenId];
        return (space.width, space.height, space.depth);
    }
    
    /**
     * @dev Count the total number of spaces owned by an address
     * @param _owner The owner address
     * @return The number of spaces owned by the address
     */
    function balanceOfSpaces(address _owner) external view returns (uint256) {
        return balanceOf(_owner);
    }
    
    /**
     * @dev Checks if a space is verified
     * @param _tokenId The ID of the token
     * @return Whether the space is verified
     */
    function isSpaceVerified(uint256 _tokenId) external view returns (bool) {
        require(_exists(_tokenId), "Token does not exist");
        return virtualSpaces[_tokenId].verified;
    }
    
    /**
     * @dev Calculate volume of a virtual space
     * @param _tokenId The ID of the token
     * @return The volume of the virtual space
     */
    function calculateSpaceVolume(uint256 _tokenId) external view returns (uint256) {
        require(_exists(_tokenId), "Token does not exist");
        VirtualSpace memory space = virtualSpaces[_tokenId];
        return space.width.mul(space.height).mul(space.depth);
    }
}
