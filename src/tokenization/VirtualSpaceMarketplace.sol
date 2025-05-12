// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./VirtualSpaceToken.sol";

/**
 * @title VirtualSpaceMarketplace
 * @dev Marketplace for virtual space NFTs
 */
contract VirtualSpaceMarketplace is ReentrancyGuard, Ownable {
    using Counters for Counters.Counter;
    using SafeMath for uint256;
    
    // Listing counter
    Counters.Counter private _listingIds;
    
    // Value assessment system
    address public valueAssessmentSystem;
    
    // Platform fee in basis points (e.g., 250 = 2.5%)
    uint256 public platformFeePercent = 250;
    
    // Maximum platform fee percent (5%)
    uint256 public constant MAX_PLATFORM_FEE = 500;
    
    // Listing structure
    struct Listing {
        uint256 listingId;
        address tokenContract;
        uint256 tokenId;
        address seller;
        uint256 price;
        uint256 appraiseValue;
        bool isActive;
        uint256 createdAt;
        uint256 updatedAt;
    }
    
    // Auction structure
    struct Auction {
        uint256 listingId;
        uint256 startPrice;
        uint256 reservePrice;
        uint256 highestBid;
        address highestBidder;
        uint256 endTime;
        bool isActive;
    }
    
    // Transaction history
    struct Transaction {
        uint256 listingId;
        address seller;
        address buyer;
        uint256 price;
        uint256 timestamp;
    }
    
    // Mappings
    mapping(uint256 => Listing) public listings;
    mapping(uint256 => Auction) public auctions;
    mapping(uint256 => Transaction[]) public listingTransactions;
    mapping(address => mapping(uint256 => bool)) public tokenListings;
    mapping(address => uint256[]) public userListings;
    mapping(address => uint256[]) public userPurchases;
    
    // Events
    event ListingCreated(uint256 indexed listingId, address indexed tokenContract, uint256 indexed tokenId, address seller, uint256 price);
    event ListingUpdated(uint256 indexed listingId, uint256 newPrice);
    event ListingCancelled(uint256 indexed listingId);
    event ListingSold(uint256 indexed listingId, address buyer, uint256 price);
    event AuctionCreated(uint256 indexed listingId, uint256 startPrice, uint256 reservePrice, uint256 endTime);
    event AuctionBid(uint256 indexed listingId, address bidder, uint256 bidAmount);
    event AuctionEnded(uint256 indexed listingId, address winner, uint256 price);
    event ValueAssessmentSystemUpdated(address indexed previousSystem, address indexed newSystem);
    event PlatformFeeUpdated(uint256 oldFee, uint256 newFee);
    
    /**
     * @dev Constructor
     */
    constructor() {
        valueAssessmentSystem = msg.sender;
    }
    
    /**
     * @dev Set the value assessment system address
     * @param _system The new value assessment system address
     */
    function setValueAssessmentSystem(address _system) external onlyOwner {
        require(_system != address(0), "Invalid address");
        emit ValueAssessmentSystemUpdated(valueAssessmentSystem, _system);
        valueAssessmentSystem = _system;
    }
    
    /**
     * @dev Set the platform fee percentage
     * @param _feePercent The new fee percentage in basis points
     */
    function setPlatformFeePercent(uint256 _feePercent) external onlyOwner {
        require(_feePercent <= MAX_PLATFORM_FEE, "Fee too high");
        emit PlatformFeeUpdated(platformFeePercent, _feePercent);
        platformFeePercent = _feePercent;
    }
    
    /**
     * @dev Create a new listing
     * @param _tokenContract Address of the token contract
     * @param _tokenId Token ID
     * @param _price Listing price
     * @return The new listing ID
     */
    function createListing(
        address _tokenContract, 
        uint256 _tokenId, 
        uint256 _price
    ) 
        external
        nonReentrant
        returns (uint256)
    {
        require(_price > 0, "Price must be greater than zero");
        require(_tokenContract != address(0), "Invalid token contract");
        
        // Check token ownership and approval
        IERC721 tokenContract = IERC721(_tokenContract);
        require(tokenContract.ownerOf(_tokenId) == msg.sender, "Not the token owner");
        require(tokenContract.isApprovedForAll(msg.sender, address(this)) || 
                tokenContract.getApproved(_tokenId) == address(this),
                "Marketplace not approved");
        
        // Check if token is already listed
        require(!tokenListings[_tokenContract][_tokenId], "Token already listed");
        
        // Generate listing ID
        _listingIds.increment();
        uint256 listingId = _listingIds.current();
        
        // Set appraise value to price initially
        uint256 appraiseValue = _price;
        
        // If the token is a VirtualSpaceToken, try to get a proper appraisal
        if (valueAssessmentSystem != address(0)) {
            // In a real implementation, this would call an external assessment service
            // For now, we'll just use the listing price
            try VirtualSpaceToken(_tokenContract).isSpaceVerified(_tokenId) returns (bool isVerified) {
                if (isVerified) {
                    // Add a verification premium to appraise value (10%)
                    appraiseValue = _price.mul(110).div(100);
                }
            } catch {
                // Not a VirtualSpaceToken or verification failed
            }
        }
        
        // Create listing
        listings[listingId] = Listing({
            listingId: listingId,
            tokenContract: _tokenContract,
            tokenId: _tokenId,
            seller: msg.sender,
            price: _price,
            appraiseValue: appraiseValue,
            isActive: true,
            createdAt: block.timestamp,
            updatedAt: block.timestamp
        });
        
        // Update mappings
        tokenListings[_tokenContract][_tokenId] = true;
        userListings[msg.sender].push(listingId);
        
        emit ListingCreated(listingId, _tokenContract, _tokenId, msg.sender, _price);
        
        return listingId;
    }
    
    /**
     * @dev Update listing price
     * @param _listingId Listing ID
     * @param _newPrice New price
     */
    function updateListingPrice(uint256 _listingId, uint256 _newPrice) external nonReentrant {
        require(_newPrice > 0, "Price must be greater than zero");
        
        Listing storage listing = listings[_listingId];
        require(listing.isActive, "Listing not active");
        require(listing.seller == msg.sender, "Not the seller");
        
        listing.price = _newPrice;
        listing.updatedAt = block.timestamp;
        
        emit ListingUpdated(_listingId, _newPrice);
    }
    
    /**
     * @dev Cancel a listing
     * @param _listingId Listing ID
     */
    function cancelListing(uint256 _listingId) external nonReentrant {
        Listing storage listing = listings[_listingId];
        require(listing.isActive, "Listing not active");
        require(listing.seller == msg.sender || msg.sender == owner(), "Not authorized");
        
        listing.isActive = false;
        tokenListings[listing.tokenContract][listing.tokenId] = false;
        
        emit ListingCancelled(_listingId);
    }
    
    /**
     * @dev Buy a listed token
     * @param _listingId Listing ID
     */
    function buyListing(uint256 _listingId) external payable nonReentrant {
        Listing storage listing = listings[_listingId];
        require(listing.isActive, "Listing not active");
        require(msg.value >= listing.price, "Insufficient payment");
        require(msg.sender != listing.seller, "Seller cannot buy");
        
        // Calculate platform fee
        uint256 platformFee = listing.price.mul(platformFeePercent).div(10000);
        uint256 sellerAmount = listing.price.sub(platformFee);
        
        // Update listing status
        listing.isActive = false;
        tokenListings[listing.tokenContract][listing.tokenId] = false;
        
        // Transfer funds
        payable(owner()).transfer(platformFee);
        payable(listing.seller).transfer(sellerAmount);
        
        // Refund excess payment
        if (msg.value > listing.price) {
            payable(msg.sender).transfer(msg.value.sub(listing.price));
        }
        
        // Transfer token
        IERC721(listing.tokenContract).safeTransferFrom(listing.seller, msg.sender, listing.tokenId);
        
        // Record transaction
        Transaction memory transaction = Transaction({
            listingId: _listingId,
            seller: listing.seller,
            buyer: msg.sender,
            price: listing.price,
            timestamp: block.timestamp
        });
        
        listingTransactions[_listingId].push(transaction);
        userPurchases[msg.sender].push(_listingId);
        
        emit ListingSold(_listingId, msg.sender, listing.price);
    }
    
    /**
     * @dev Create an auction for a token
     * @param _tokenContract Address of the token contract
     * @param _tokenId Token ID
     * @param _startPrice Starting price
     * @param _reservePrice Reserve price
     * @param _duration Auction duration in seconds
     * @return The new listing ID
     */
    function createAuction(
        address _tokenContract,
        uint256 _tokenId,
        uint256 _startPrice,
        uint256 _reservePrice,
        uint256 _duration
    )
        external
        nonReentrant
        returns (uint256)
    {
        require(_startPrice > 0, "Start price must be greater than zero");
        require(_reservePrice >= _startPrice, "Reserve price must be greater than or equal to start price");
        require(_duration >= 1 hours && _duration <= 7 days, "Duration must be between 1 hour and 7 days");
        
        // Check token ownership and approval
        IERC721 tokenContract = IERC721(_tokenContract);
        require(tokenContract.ownerOf(_tokenId) == msg.sender, "Not the token owner");
        require(tokenContract.isApprovedForAll(msg.sender, address(this)) || 
                tokenContract.getApproved(_tokenId) == address(this),
                "Marketplace not approved");
        
        // Check if token is already listed
        require(!tokenListings[_tokenContract][_tokenId], "Token already listed");
        
        // Generate listing ID
        _listingIds.increment();
        uint256 listingId = _listingIds.current();
        
        // Set appraise value to reserve price initially
        uint256 appraiseValue = _reservePrice;
        
        // If the token is a VirtualSpaceToken, try to get a proper appraisal
        if (valueAssessmentSystem != address(0)) {
            // In a real implementation, this would call an external assessment service
            // For now, we'll just use the reserve price
            try VirtualSpaceToken(_tokenContract).isSpaceVerified(_tokenId) returns (bool isVerified) {
                if (isVerified) {
                    // Add a verification premium to appraise value (10%)
                    appraiseValue = _reservePrice.mul(110).div(100);
                }
            } catch {
                // Not a VirtualSpaceToken or verification failed
            }
        }
        
        // Create listing
        listings[listingId] = Listing({
            listingId: listingId,
            tokenContract: _tokenContract,
            tokenId: _tokenId,
            seller: msg.sender,
            price: _startPrice, // Initial price is the start price
            appraiseValue: appraiseValue,
            isActive: true,
            createdAt: block.timestamp,
            updatedAt: block.timestamp
        });
        
        // Create auction
        auctions[listingId] = Auction({
            listingId: listingId,
            startPrice: _startPrice,
            reservePrice: _reservePrice,
            highestBid: 0,
            highestBidder: address(0),
            endTime: block.timestamp + _duration,
            isActive: true
        });
        
        // Update mappings
        tokenListings[_tokenContract][_tokenId] = true;
        userListings[msg.sender].push(listingId);
        
        emit ListingCreated(listingId, _tokenContract, _tokenId, msg.sender, _startPrice);
        emit AuctionCreated(listingId, _startPrice, _reservePrice, block.timestamp + _duration);
        
        return listingId;
    }
    
    /**
     * @dev Place a bid on an auction
     * @param _listingId Listing ID
     */
    function placeBid(uint256 _listingId) external payable nonReentrant {
        Listing storage listing = listings[_listingId];
        Auction storage auction = auctions[_listingId];
        
        require(listing.isActive && auction.isActive, "Auction not active");
        require(block.timestamp < auction.endTime, "Auction ended");
        require(msg.sender != listing.seller, "Seller cannot bid");
        
        if (auction.highestBid == 0) {
            // First bid must be at least start price
            require(msg.value >= auction.startPrice, "Bid too low");
        } else {
            // Subsequent bids must be at least 5% higher than the highest bid
            uint256 minBid = auction.highestBid.mul(105).div(100);
            require(msg.value >= minBid, "Bid too low");
            
            // Refund the previous highest bidder
            payable(auction.highestBidder).transfer(auction.highestBid);
        }
        
        // Update highest bid
        auction.highestBid = msg.value;
        auction.highestBidder = msg.sender;
        
        emit AuctionBid(_listingId, msg.sender, msg.value);
    }
    
    /**
     * @dev End an auction
     * @param _listingId Listing ID
     */
    function endAuction(uint256 _listingId) external nonReentrant {
        Listing storage listing = listings[_listingId];
        Auction storage auction = auctions[_listingId];
        
        require(listing.isActive && auction.isActive, "Auction not active");
        require(block.timestamp >= auction.endTime || msg.sender == owner(), "Auction not ended yet");
        
        auction.isActive = false;
        listing.isActive = false;
        tokenListings[listing.tokenContract][listing.tokenId] = false;
        
        if (auction.highestBid >= auction.reservePrice && auction.highestBidder != address(0)) {
            // Auction successful
            
            // Calculate platform fee
            uint256 platformFee = auction.highestBid.mul(platformFeePercent).div(10000);
            uint256 sellerAmount = auction.highestBid.sub(platformFee);
            
            // Transfer funds
            payable(owner()).transfer(platformFee);
            payable(listing.seller).transfer(sellerAmount);
            
            // Transfer token
            IERC721(listing.tokenContract).safeTransferFrom(listing.seller, auction.highestBidder, listing.tokenId);
            
            // Record transaction
            Transaction memory transaction = Transaction({
                listingId: _listingId,
                seller: listing.seller,
                buyer: auction.highestBidder,
                price: auction.highestBid,
                timestamp: block.timestamp
            });
            
            listingTransactions[_listingId].push(transaction);
            userPurchases[auction.highestBidder].push(_listingId);
            
            emit ListingSold(_listingId, auction.highestBidder, auction.highestBid);
            emit AuctionEnded(_listingId, auction.highestBidder, auction.highestBid);
        } else {
            // Auction failed (no bidder or reserve price not met)
            if (auction.highestBidder != address(0)) {
                // Refund the highest bidder
                payable(auction.highestBidder).transfer(auction.highestBid);
            }
            
            emit AuctionEnded(_listingId, address(0), 0);
        }
    }
    
    /**
     * @dev Set an appraise value for a listing (only by value assessment system)
     * @param _listingId Listing ID
     * @param _appraiseValue New appraise value
     */
    function setAppraiseValue(uint256 _listingId, uint256 _appraiseValue) external {
        require(msg.sender == valueAssessmentSystem || msg.sender == owner(), "Not authorized");
        
        Listing storage listing = listings[_listingId];
        require(listing.isActive, "Listing not active");
        
        listing.appraiseValue = _appraiseValue;
        listing.updatedAt = block.timestamp;
    }
    
    /**
     * @dev Get listing details
     * @param _listingId Listing ID
     * @return The listing details
     */
    function getListing(uint256 _listingId) external view returns (Listing memory) {
        return listings[_listingId];
    }
    
    /**
     * @dev Get auction details
     * @param _listingId Listing ID
     * @return The auction details
     */
    function getAuction(uint256 _listingId) external view returns (Auction memory) {
        return auctions[_listingId];
    }
    
    /**
     * @dev Get transaction history for a listing
     * @param _listingId Listing ID
     * @return The transaction history
     */
    function getTransactionHistory(uint256 _listingId) external view returns (Transaction[] memory) {
        return listingTransactions[_listingId];
    }
    
    /**
     * @dev Get all listings by a user
     * @param _user User address
     * @return Array of listing IDs
     */
    function getUserListings(address _user) external view returns (uint256[] memory) {
        return userListings[_user];
    }
    
    /**
     * @dev Get all purchases by a user
     * @param _user User address
     * @return Array of listing IDs
     */
    function getUserPurchases(address _user) external view returns (uint256[] memory) {
        return userPurchases[_user];
    }
    
    /**
     * @dev Check if a token is listed
     * @param _tokenContract Token contract address
     * @param _tokenId Token ID
     * @return Whether the token is listed
     */
    function isTokenListed(address _tokenContract, uint256 _tokenId) external view returns (bool) {
        return tokenListings[_tokenContract][_tokenId];
    }
    
    /**
     * @dev Get the total number of listings
     * @return The total number of listings
     */
    function getTotalListings() external view returns (uint256) {
        return _listingIds.current();
    }
    
    /**
     * @dev Withdraw accumulated platform fees (only owner)
     */
    function withdrawFees() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No fees to withdraw");
        
        payable(owner()).transfer(balance);
    }
}
