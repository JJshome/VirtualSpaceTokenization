# Virtual Space Tokenization Simulation

This directory contains simulation tools for testing and demonstrating the AI-based Virtual Space Tokenization and Trading System.

## Overview

The simulation environment allows users to:

1. Generate virtual spaces using AI algorithms
2. Tokenize virtual spaces into NFTs
3. Simulate trading and value assessment
4. Visualize virtual space interactions
5. Test performance under various network conditions

## Getting Started

### Prerequisites

- Node.js 18.0 or higher
- Python 3.9 or higher
- TensorFlow 2.10 or higher
- Web3.js 1.8.0 or higher
- Three.js for 3D visualization

### Installation

```bash
# Install dependencies
npm install

# Install Python requirements
pip install -r requirements.txt

# Set up local blockchain for testing
npm run setup-local-blockchain
```

### Running the Simulation

```bash
# Start the simulation server
npm run simulation

# Launch the web interface
npm run web-ui
```

## Features

### Virtual Space Generation

The simulation includes AI-based virtual space generation with configurable parameters:

- Space dimensions
- Theme/style
- Environmental features
- Object density
- Lighting conditions

### Tokenization Simulation

Demonstrates the tokenization process with the following features:

- Smart contract deployment
- NFT minting
- Metadata generation
- Digital asset registration

### Value Assessment

The AI value assessment system considers multiple factors:

- Location within the virtual world
- Proximity to high-traffic areas
- Design quality score
- Utility and functionality
- Scarcity metrics

### Trade Simulation

Simulates a marketplace with:

- Peer-to-peer trading
- Auction mechanisms
- Price history visualization
- Market trends analysis

## Configuration

The simulation behavior can be configured in the `simulation-config.json` file:

```json
{
  "networkLatency": 5,
  "nodeCount": 10,
  "initialSpaceCount": 50,
  "simulatedUsers": 100,
  "tradingFrequency": "medium",
  "valuationAlgorithm": "comprehensive"
}
```

## API Reference

The simulation exposes a REST API for integration with external tools:

- `GET /api/spaces` - List all virtual spaces
- `POST /api/spaces` - Create a new virtual space
- `GET /api/spaces/{id}` - Get details of a specific space
- `POST /api/spaces/{id}/tokenize` - Tokenize a virtual space
- `GET /api/marketplace` - Get marketplace statistics
- `POST /api/transactions` - Create a new transaction
