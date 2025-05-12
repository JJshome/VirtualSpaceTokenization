#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SpaceGenerator.py - AI-based virtual space generation module for the 
Virtual Space Tokenization System.

This module provides the core functionality for generating virtual spaces
based on user specifications using advanced AI techniques including
natural language processing, generative adversarial networks, and
style transfer algorithms.
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import random
from typing import Dict, List, Tuple, Union, Optional

# Set up GPU memory growth to avoid OOM errors
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

# Constants
DEFAULT_RESOLUTION = 256
MAX_RESOLUTION = 1024
DEFAULT_ROOM_COUNT = 3
DEFAULT_OBJECT_COUNT = 20
DEFAULT_STYLE = "modern"
SUPPORTED_STYLES = ["modern", "futuristic", "natural", "fantasy", "cyberpunk", "minimalist"]
SUPPORTED_OBJECTS = ["chair", "table", "light", "plant", "wall", "floor", "ceiling", "window", "door"]

class SpaceGenerator:
    """
    AI-based virtual space generator class that creates virtual spaces
    based on user specifications.
    """
    
    def __init__(self, model_path: str = None, config_path: str = None):
        """
        Initialize the SpaceGenerator with optional model and configuration paths.
        
        Args:
            model_path: Path to the pre-trained model files
            config_path: Path to the configuration file
        """
        self.model_path = model_path
        self.config = self._load_config(config_path)
        self.models = {}
        self.initialized = False
        
        # Load models
        try:
            self._initialize_models()
            self.initialized = True
            print("SpaceGenerator initialized successfully")
        except Exception as e:
            print(f"Error initializing models: {e}")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing configuration parameters
        """
        default_config = {
            "resolution": DEFAULT_RESOLUTION,
            "max_resolution": MAX_RESOLUTION,
            "default_room_count": DEFAULT_ROOM_COUNT,
            "default_object_count": DEFAULT_OBJECT_COUNT,
            "default_style": DEFAULT_STYLE,
            "supported_styles": SUPPORTED_STYLES,
            "supported_objects": SUPPORTED_OBJECTS,
            "use_homomorphic_encryption": False,
            "use_edge_ai": True,
            "model_params": {
                "latent_dim": 256,
                "style_dim": 64,
                "layout_encoder_layers": 4,
                "object_generator_layers": 3
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if isinstance(value, dict) and key in default_config and isinstance(default_config[key], dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Error loading config, using defaults: {e}")
        
        return default_config
    
    def _initialize_models(self):
        """Initialize AI models required for space generation."""
        # In a real implementation, this would load pre-trained models
        # For demonstration purposes, we'll create simple models
        
        # Text encoder model (processes natural language descriptions)
        text_input = keras.Input(shape=(None,), dtype=tf.int32, name="text_input")
        embedding = layers.Embedding(10000, 256)(text_input)
        lstm = layers.LSTM(256)(embedding)
        text_encoder = keras.Model(text_input, lstm, name="text_encoder")
        self.models["text_encoder"] = text_encoder
        
        # Layout generator model
        latent_dim = self.config["model_params"]["latent_dim"]
        layout_input = keras.Input(shape=(latent_dim,), name="layout_input")
        x = layers.Dense(512, activation="relu")(layout_input)
        x = layers.Dense(1024, activation="relu")(x)
        x = layers.Dense(2048, activation="relu")(x)
        layout_output = layers.Dense(64*64*3, activation="tanh")(x)
        layout_output = layers.Reshape((64, 64, 3))(layout_output)
        layout_generator = keras.Model(layout_input, layout_output, name="layout_generator")
        self.models["layout_generator"] = layout_generator
        
        # Style transfer model
        style_input = keras.Input(shape=(self.config["model_params"]["style_dim"],), name="style_input")
        content_input = keras.Input(shape=(64, 64, 3), name="content_input")
        
        # Combine style and content
        style_expanded = layers.Dense(64*64)(style_input)
        style_expanded = layers.Reshape((64, 64, 1))(style_expanded)
        combined = layers.Concatenate()([content_input, style_expanded])
        
        # Style transfer network
        x = layers.Conv2D(64, (3, 3), padding="same", activation="relu")(combined)
        x = layers.Conv2D(128, (3, 3), padding="same", activation="relu")(x)
        x = layers.UpSampling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), padding="same", activation="relu")(x)
        x = layers.UpSampling2D((2, 2))(x)
        style_output = layers.Conv2D(3, (3, 3), padding="same", activation="tanh")(x)
        
        style_transfer = keras.Model([content_input, style_input], style_output, name="style_transfer")
        self.models["style_transfer"] = style_transfer
        
        # Object placement model
        object_input = keras.Input(shape=(latent_dim + 5,), name="object_input")  # Latent + object type + location (x,y,z)
        x = layers.Dense(256, activation="relu")(object_input)
        x = layers.Dense(512, activation="relu")(x)
        object_output = layers.Dense(9, activation="sigmoid")(x)  # Position, rotation, scale
        object_placement = keras.Model(object_input, object_output, name="object_placement")
        self.models["object_placement"] = object_placement
    
    def generate_space(self, 
                     description: str,
                     size: Tuple[float, float, float] = (100.0, 50.0, 100.0),
                     style: str = None,
                     room_count: int = None,
                     object_density: float = 0.5) -> Dict:
        """
        Generate a virtual space based on the provided parameters.
        
        Args:
            description: Text description of the desired space
            size: Tuple of (width, height, depth) in meters
            style: Visual style for the space
            room_count: Number of rooms to generate
            object_density: Density of objects (0.0 to 1.0)
            
        Returns:
            Dictionary containing the generated space data
        """
        if not self.initialized:
            raise RuntimeError("SpaceGenerator not properly initialized")
        
        # Set defaults if not provided
        style = style or self.config["default_style"]
        if style not in self.config["supported_styles"]:
            print(f"Warning: Style '{style}' not supported. Using '{DEFAULT_STYLE}' instead.")
            style = DEFAULT_STYLE
        
        room_count = room_count or self.config["default_room_count"]
        
        # Process the text description
        text_features = self._process_description(description)
        
        # Generate the basic layout
        layout = self._generate_layout(text_features, size, room_count)
        
        # Apply style transfer
        styled_layout = self._apply_style(layout, style)
        
        # Place objects
        objects = self._place_objects(styled_layout, text_features, object_density)
        
        # Final assembly and metadata
        result = {
            "layout": styled_layout,
            "objects": objects,
            "metadata": {
                "description": description,
                "size": size,
                "style": style,
                "room_count": room_count,
                "object_count": len(objects),
                "generation_params": {
                    "object_density": object_density,
                    "resolution": self.config["resolution"],
                }
            }
        }
        
        return result
    
    def _process_description(self, description: str) -> np.ndarray:
        """
        Process natural language description into features for the generator.
        
        Args:
            description: Text description of the desired space
            
        Returns:
            Numpy array of extracted features
        """
        # In a real implementation, this would use NLP to extract meaningful features
        # For demonstration, we'll create a random feature vector
        # The size matches the latent dimension from config
        latent_dim = self.config["model_params"]["latent_dim"]
        
        # Create a deterministic but varied vector based on the description
        # This is a simple hash function to convert text to a consistent vector
        import hashlib
        hash_object = hashlib.md5(description.encode())
        seed = int(hash_object.hexdigest(), 16) % (2**32)
        np.random.seed(seed)
        
        features = np.random.normal(0, 1, latent_dim)
        return features
    
    def _generate_layout(self, 
                        text_features: np.ndarray, 
                        size: Tuple[float, float, float],
                        room_count: int) -> Dict:
        """
        Generate the basic spatial layout of the virtual space.
        
        Args:
            text_features: Features extracted from the description
            size: Dimensions of the space
            room_count: Number of rooms to generate
            
        Returns:
            Dictionary containing layout information
        """
        width, height, depth = size
        
        # Generate rooms
        rooms = []
        available_space = np.ones((int(width), int(depth)), dtype=bool)
        
        for i in range(room_count):
            # Try to find an empty space for the room
            room_width = random.randint(int(width/6), int(width/3))
            room_depth = random.randint(int(depth/6), int(depth/3))
            
            # Find suitable position
            attempts = 0
            placed = False
            
            while attempts < 100 and not placed:
                x = random.randint(0, int(width - room_width))
                z = random.randint(0, int(depth - room_depth))
                
                # Check if space is available
                if np.all(available_space[x:x+room_width, z:z+room_depth]):
                    available_space[x:x+room_width, z:z+room_depth] = False
                    placed = True
                
                attempts += 1
            
            if placed:
                room = {
                    "id": f"room_{i}",
                    "position": [x, 0, z],
                    "size": [room_width, height, room_depth],
                    "connections": []
                }
                rooms.append(room)
        
        # Connect rooms (create doorways)
        for i in range(len(rooms)):
            for j in range(i+1, len(rooms)):
                # Determine if rooms should be connected
                if random.random() < 0.7:  # 70% chance of connection
                    rooms[i]["connections"].append(rooms[j]["id"])
                    rooms[j]["connections"].append(rooms[i]["id"])
        
        # Generate walls, floors, and ceilings
        surfaces = []
        
        # Main floor
        surfaces.append({
            "type": "floor",
            "position": [width/2, 0, depth/2],
            "size": [width, 0.1, depth],
            "material": "default"
        })
        
        # Main ceiling
        surfaces.append({
            "type": "ceiling",
            "position": [width/2, height, depth/2],
            "size": [width, 0.1, depth],
            "material": "default"
        })
        
        # Outer walls
        surfaces.append({
            "type": "wall",
            "position": [width/2, height/2, 0],
            "size": [width, height, 0.1],
            "material": "default"
        })
        
        surfaces.append({
            "type": "wall",
            "position": [width/2, height/2, depth],
            "size": [width, height, 0.1],
            "material": "default"
        })
        
        surfaces.append({
            "type": "wall",
            "position": [0, height/2, depth/2],
            "size": [0.1, height, depth],
            "material": "default"
        })
        
        surfaces.append({
            "type": "wall",
            "position": [width, height/2, depth/2],
            "size": [0.1, height, depth],
            "material": "default"
        })
        
        # Add inner walls for rooms
        for room in rooms:
            x, y, z = room["position"]
            w, h, d = room["size"]
            
            # Room-specific walls, only where needed
            if not np.any(available_space[x-1:x, z:z+d]):
                surfaces.append({
                    "type": "wall",
                    "position": [x, h/2, z+d/2],
                    "size": [0.1, h, d],
                    "material": "default"
                })
            
            if not np.any(available_space[x+w:x+w+1, z:z+d]):
                surfaces.append({
                    "type": "wall",
                    "position": [x+w, h/2, z+d/2],
                    "size": [0.1, h, d],
                    "material": "default"
                })
            
            if not np.any(available_space[x:x+w, z-1:z]):
                surfaces.append({
                    "type": "wall",
                    "position": [x+w/2, h/2, z],
                    "size": [w, h, 0.1],
                    "material": "default"
                })
            
            if not np.any(available_space[x:x+w, z+d:z+d+1]):
                surfaces.append({
                    "type": "wall",
                    "position": [x+w/2, h/2, z+d],
                    "size": [w, h, 0.1],
                    "material": "default"
                })
        
        # Add doorways
        doorways = []
        for room in rooms:
            x, y, z = room["position"]
            w, h, d = room["size"]
            
            for connection in room["connections"]:
                connected_room = next((r for r in rooms if r["id"] == connection), None)
                if connected_room:
                    cx, cy, cz = connected_room["position"]
                    cw, ch, cd = connected_room["size"]
                    
                    # Create a doorway between the rooms
                    if (x <= cx + cw and x + w >= cx):  # Rooms overlap in x-axis
                        # Create doorway in z-direction
                        door_x = max(x, cx) + abs(max(x, cx) - min(x+w, cx+cw)) / 2
                        door_z = min(z+d, cz) if z < cz else min(cz+cd, z)
                        
                        doorways.append({
                            "position": [door_x, 0, door_z],
                            "rotation": [0, 90, 0],
                            "size": [2.0, 2.1, 0.1]
                        })
                    
                    elif (z <= cz + cd and z + d >= cz):  # Rooms overlap in z-axis
                        # Create doorway in x-direction
                        door_x = min(x+w, cx) if x < cx else min(cx+cw, x)
                        door_z = max(z, cz) + abs(max(z, cz) - min(z+d, cz+cd)) / 2
                        
                        doorways.append({
                            "position": [door_x, 0, door_z],
                            "rotation": [0, 0, 0],
                            "size": [2.0, 2.1, 0.1]
                        })
        
        layout = {
            "dimensions": list(size),
            "rooms": rooms,
            "surfaces": surfaces,
            "doorways": doorways
        }
        
        return layout
    
    def _apply_style(self, layout: Dict, style: str) -> Dict:
        """
        Apply a specific visual style to the layout.
        
        Args:
            layout: Basic layout structure
            style: Style identifier
            
        Returns:
            Layout with style information added
        """
        # Create a copy of the layout
        styled_layout = layout.copy()
        
        # Material definitions based on style
        materials = {}
        
        if style == "modern":
            materials = {
                "wall": {"color": [0.95, 0.95, 0.95], "roughness": 0.1, "metallic": 0.0},
                "floor": {"color": [0.7, 0.7, 0.7], "roughness": 0.2, "metallic": 0.0},
                "ceiling": {"color": [0.98, 0.98, 0.98], "roughness": 0.1, "metallic": 0.0},
                "accent": {"color": [0.2, 0.4, 0.8], "roughness": 0.2, "metallic": 0.0}
            }
        elif style == "futuristic":
            materials = {
                "wall": {"color": [0.1, 0.1, 0.12], "roughness": 0.05, "metallic": 0.5},
                "floor": {"color": [0.2, 0.2, 0.22], "roughness": 0.1, "metallic": 0.7},
                "ceiling": {"color": [0.05, 0.05, 0.08], "roughness": 0.05, "metallic": 0.5},
                "accent": {"color": [0.0, 0.8, 0.9], "roughness": 0.1, "metallic": 0.8}
            }
        elif style == "natural":
            materials = {
                "wall": {"color": [0.9, 0.85, 0.78], "roughness": 0.8, "metallic": 0.0},
                "floor": {"color": [0.65, 0.55, 0.45], "roughness": 0.9, "metallic": 0.0},
                "ceiling": {"color": [0.9, 0.87, 0.82], "roughness": 0.7, "metallic": 0.0},
                "accent": {"color": [0.2, 0.6, 0.3], "roughness": 0.8, "metallic": 0.0}
            }
        elif style == "fantasy":
            materials = {
                "wall": {"color": [0.8, 0.7, 0.9], "roughness": 0.5, "metallic": 0.1},
                "floor": {"color": [0.6, 0.5, 0.7], "roughness": 0.6, "metallic": 0.1},
                "ceiling": {"color": [0.7, 0.6, 0.8], "roughness": 0.5, "metallic": 0.1},
                "accent": {"color": [0.9, 0.5, 0.9], "roughness": 0.4, "metallic": 0.2}
            }
        elif style == "cyberpunk":
            materials = {
                "wall": {"color": [0.1, 0.1, 0.15], "roughness": 0.3, "metallic": 0.2, "emissive": [0.0, 0.0, 0.05]},
                "floor": {"color": [0.15, 0.15, 0.2], "roughness": 0.4, "metallic": 0.3},
                "ceiling": {"color": [0.05, 0.05, 0.1], "roughness": 0.3, "metallic": 0.2, "emissive": [0.0, 0.0, 0.05]},
                "accent": {"color": [0.9, 0.2, 0.6], "roughness": 0.3, "metallic": 0.4, "emissive": [0.5, 0.1, 0.3]}
            }
        else:  # Default to minimalist
            materials = {
                "wall": {"color": [1.0, 1.0, 1.0], "roughness": 0.05, "metallic": 0.0},
                "floor": {"color": [0.9, 0.9, 0.9], "roughness": 0.1, "metallic": 0.0},
                "ceiling": {"color": [1.0, 1.0, 1.0], "roughness": 0.05, "metallic": 0.0},
                "accent": {"color": [0.0, 0.0, 0.0], "roughness": 0.05, "metallic": 0.0}
            }
        
        # Apply materials to surfaces
        for surface in styled_layout["surfaces"]:
            if surface["type"] == "wall":
                surface["material"] = materials["wall"].copy()
            elif surface["type"] == "floor":
                surface["material"] = materials["floor"].copy()
            elif surface["type"] == "ceiling":
                surface["material"] = materials["ceiling"].copy()
            else:
                surface["material"] = materials["accent"].copy()
        
        # Add lighting based on style
        lights = []
        
        # Main light sources
        if style == "modern" or style == "minimalist":
            # Ceiling lights in each room
            for room in styled_layout["rooms"]:
                x, y, z = room["position"]
                w, h, d = room["size"]
                lights.append({
                    "type": "point",
                    "position": [x + w/2, h - 0.5, z + d/2],
                    "color": [1.0, 0.98, 0.92],
                    "intensity": 0.8,
                    "range": max(w, d) * 1.5
                })
        
        elif style == "futuristic" or style == "cyberpunk":
            # Strip lights and accent lighting
            for room in styled_layout["rooms"]:
                x, y, z = room["position"]
                w, h, d = room["size"]
                
                # Ceiling strip
                lights.append({
                    "type": "rect",
                    "position": [x + w/2, h - 0.1, z + d/2],
                    "size": [w * 0.8, 0.1, d * 0.8],
                    "color": [0.9, 0.95, 1.0] if style == "futuristic" else [0.5, 0.0, 1.0],
                    "intensity": 0.6,
                    "range": max(w, d) * 1.2
                })
                
                # Wall accents
                if style == "cyberpunk":
                    lights.append({
                        "type": "rect",
                        "position": [x, h/2, z + d/2],
                        "size": [0.1, h * 0.5, d * 0.6],
                        "color": [0.0, 0.8, 0.9],
                        "intensity": 0.4,
                        "range": d * 0.8
                    })
        
        elif style == "natural":
            # Warm, natural lighting
            for room in styled_layout["rooms"]:
                x, y, z = room["position"]
                w, h, d = room["size"]
                
                # Main ceiling light
                lights.append({
                    "type": "point",
                    "position": [x + w/2, h - 0.5, z + d/2],
                    "color": [1.0, 0.9, 0.8],
                    "intensity": 0.7,
                    "range": max(w, d) * 1.5
                })
                
                # Additional floor lamp
                lights.append({
                    "type": "point",
                    "position": [x + w*0.25, h/3, z + d*0.25],
                    "color": [0.9, 0.8, 0.7],
                    "intensity": 0.4,
                    "range": 5.0
                })
        
        elif style == "fantasy":
            # Magical lighting effects
            for room in styled_layout["rooms"]:
                x, y, z = room["position"]
                w, h, d = room["size"]
                
                # Ambient magical glow
                lights.append({
                    "type": "point",
                    "position": [x + w/2, h/2, z + d/2],
                    "color": [0.8, 0.5, 1.0],
                    "intensity": 0.5,
                    "range": max(w, d) * 2.0
                })
                
                # Additional accent lights
                corners = [
                    [x + w*0.2, h*0.7, z + d*0.2],
                    [x + w*0.8, h*0.7, z + d*0.2],
                    [x + w*0.2, h*0.7, z + d*0.8],
                    [x + w*0.8, h*0.7, z + d*0.8]
                ]
                
                for i, corner in enumerate(corners):
                    colors = [[1.0, 0.3, 0.7], [0.3, 0.7, 1.0], [0.7, 1.0, 0.3], [0.5, 0.3, 1.0]]
                    lights.append({
                        "type": "point",
                        "position": corner,
                        "color": colors[i % len(colors)],
                        "intensity": 0.3,
                        "range": 3.0
                    })
        
        # Add ambient lighting for all styles
        lights.append({
            "type": "ambient",
            "intensity": 0.2,
            "color": [1.0, 1.0, 1.0]
        })
        
        # Add skybox/environment map based on style
        environment = {
            "modern": "modern_interior",
            "futuristic": "scifi_lab",
            "natural": "forest_clearing",
            "fantasy": "magic_sunset",
            "cyberpunk": "night_city",
            "minimalist": "studio_light"
        }
        
        styled_layout["lights"] = lights
        styled_layout["environment"] = environment.get(style, "neutral")
        styled_layout["style"] = style
        
        return styled_layout
    
    def _place_objects(self, layout: Dict, text_features: np.ndarray, density: float) -> List[Dict]:
        """
        Place objects within the virtual space.
        
        Args:
            layout: The styled layout of the space
            text_features: Features extracted from the description
            density: Density of object placement (0.0 to 1.0)
            
        Returns:
            List of object definitions
        """
        objects = []
        
        # Calculate object count based on density and room sizes
        total_area = sum(room["size"][0] * room["size"][2] for room in layout["rooms"])
        base_object_count = int(total_area * density / 10)  # One object per 10 sq meters at density 1.0
        object_count = max(5, min(base_object_count, 200))  # Limit between 5 and 200 objects
        
        # Common objects by room and style
        object_templates = {
            "modern": {
                "seating": ["sofa_modern", "chair_accent", "chair_office", "stool_bar"],
                "tables": ["table_coffee", "table_dining", "desk_modern", "counter_kitchen"],
                "storage": ["shelf_wall", "cabinet_modern", "bookcase_open"],
                "lighting": ["lamp_floor", "lamp_table", "pendant_light"],
                "decor": ["plant_potted", "rug_area", "artwork_canvas", "vase_decorative"]
            },
            "futuristic": {
                "seating": ["chair_hover", "sofa_modular", "stool_interactive"],
                "tables": ["table_floating", "desk_holographic", "console_control"],
                "storage": ["unit_wall", "locker_secure", "display_digital"],
                "lighting": ["light_ambient", "projector_hologram", "strip_led"],
                "decor": ["sculpture_dynamic", "plant_synthetic", "panel_interactive"]
            },
            "natural": {
                "seating": ["chair_wooden", "bench_rustic", "sofa_earthy", "hammock_woven"],
                "tables": ["table_log", "table_farmhouse", "desk_wooden"],
                "storage": ["shelf_reclaimed", "chest_wooden", "basket_woven"],
                "lighting": ["lamp_paper", "lantern_hanging", "sconce_organic"],
                "decor": ["plant_large", "plant_hanging", "rug_natural", "fountain_stone", "mobile_wood"]
            },
            "fantasy": {
                "seating": ["throne_ornate", "chair_enchanted", "cushion_floating"],
                "tables": ["table_crystal", "pedestal_magical", "altar_stone"],
                "storage": ["chest_treasure", "bookcase_spell", "cabinet_potion"],
                "lighting": ["crystal_glowing", "orb_magical", "lantern_fairy"],
                "decor": ["statue_mythical", "tapestry_magical", "fountain_glowing", "mirror_enchanted"]
            },
            "cyberpunk": {
                "seating": ["chair_neon", "sofa_angular", "stool_industrial"],
                "tables": ["table_terminal", "desk_tech", "bar_neon"],
                "storage": ["locker_metal", "server_rack", "crate_industrial"],
                "lighting": ["light_neon", "sign_holographic", "projector_advert"],
                "decor": ["terminal_old", "cables_exposed", "graffiti_digital", "drone_inactive"]
            },
            "minimalist": {
                "seating": ["chair_simple", "sofa_clean", "stool_minimal"],
                "tables": ["table_sleek", "desk_minimal", "surface_floating"],
                "storage": ["shelf_minimal", "cabinet_handleless", "rack_simple"],
                "lighting": ["lamp_minimal", "light_recessed", "pendant_simple"],
                "decor": ["plant_architectural", "art_minimal", "sculpture_abstract"]
            }
        }
        
        # Get style-specific objects
        style = layout.get("style", "modern")
        style_objects = object_templates.get(style, object_templates["modern"])
        
        # Flatten the list of objects
        all_objects = []
        for category in style_objects.values():
            all_objects.extend(category)
        
        # Place objects in each room
        for room in layout["rooms"]:
            x, y, z = room["position"]
            w, h, d = room["size"]
            room_area = w * d
            
            # Calculate number of objects for this room based on its area
            room_object_count = int(object_count * (room_area / total_area))
            
            # Reserve space near doors and walls
            margin = 0.5  # 0.5m margin from walls
            available_x = np.linspace(x + margin, x + w - margin, num=int(w - 2*margin))
            available_z = np.linspace(z + margin, z + d - margin, num=int(d - 2*margin))
            
            # Place objects
            for i in range(room_object_count):
                # Select random object type
                obj_type = random.choice(all_objects)
                
                # Determine object size based on type
                if "sofa" in obj_type or "table_dining" in obj_type:
                    obj_size = [2.0, 0.8, 0.8]
                elif "table" in obj_type or "desk" in obj_type:
                    obj_size = [1.2, 0.75, 0.6]
                elif "chair" in obj_type or "stool" in obj_type:
                    obj_size = [0.5, 0.8, 0.5]
                elif "lamp" in obj_type and "floor" in obj_type:
                    obj_size = [0.4, 1.5, 0.4]
                elif "plant" in obj_type and "large" in obj_type:
                    obj_size = [0.7, 1.8, 0.7]
                elif "shelf" in obj_type or "bookcase" in obj_type:
                    obj_size = [1.2, 1.8, 0.4]
                else:
                    obj_size = [0.4, 0.4, 0.4]
                
                # Find position
                pos_x = random.choice(available_x)
                pos_z = random.choice(available_z)
                
                # Object Y position (height) depends on type
                if "pendant" in obj_type:
                    pos_y = h - 1.0  # Hang from ceiling
                elif "lamp_table" in obj_type or "vase" in obj_type:
                    pos_y = 0.75  # On a table
                elif any(word in obj_type for word in ["sofa", "table", "desk", "chair", "stool"]):
                    pos_y = 0  # On the floor
                else:
                    pos_y = 0  # Default to floor
                
                # Random rotation (around Y axis)
                rotation = [0, random.uniform(0, 360), 0]
                
                # Create object definition
                obj = {
                    "type": obj_type,
                    "position": [pos_x, pos_y, pos_z],
                    "rotation": rotation,
                    "size": obj_size,
                    "material": {}  # Will be filled based on object type
                }
                
                # Add material properties based on object type and style
                if "seating" in obj_type or "sofa" in obj_type or "chair" in obj_type:
                    if style == "modern":
                        obj["material"] = {"color": [0.3, 0.3, 0.3], "roughness": 0.8}
                    elif style == "futuristic":
                        obj["material"] = {"color": [0.1, 0.1, 0.15], "roughness": 0.2, "metallic": 0.5}
                    elif style == "natural":
                        obj["material"] = {"color": [0.6, 0.5, 0.4], "roughness": 0.9}
                    elif style == "fantasy":
                        obj["material"] = {"color": [0.7, 0.3, 0.7], "roughness": 0.5, "metallic": 0.2}
                    elif style == "cyberpunk":
                        obj["material"] = {"color": [0.2, 0.2, 0.2], "roughness": 0.3, "metallic": 0.7, "emissive": [0.0, 0.1, 0.2]}
                    else:  # minimalist
                        obj["material"] = {"color": [0.9, 0.9, 0.9], "roughness": 0.5}
                
                elif "table" in obj_type or "desk" in obj_type:
                    if style == "modern":
                        obj["material"] = {"color": [0.8, 0.8, 0.8], "roughness": 0.3, "metallic": 0.1}
                    elif style == "futuristic":
                        obj["material"] = {"color": [0.9, 0.9, 0.95], "roughness": 0.1, "metallic": 0.8}
                    elif style == "natural":
                        obj["material"] = {"color": [0.5, 0.4, 0.3], "roughness": 0.8}
                    elif style == "fantasy":
                        obj["material"] = {"color": [0.4, 0.5, 0.6], "roughness": 0.3, "metallic": 0.5}
                    elif style == "cyberpunk":
                        obj["material"] = {"color": [0.1, 0.1, 0.1], "roughness": 0.2, "metallic": 0.9}
                    else:  # minimalist
                        obj["material"] = {"color": [1.0, 1.0, 1.0], "roughness": 0.2}
                
                elif "lamp" in obj_type or "light" in obj_type:
                    # Add light component
                    light_color = [1.0, 0.9, 0.8]  # Warm light by default
                    
                    if style == "futuristic":
                        light_color = [0.9, 0.95, 1.0]  # Cool light
                    elif style == "fantasy":
                        light_color = [0.8, 0.7, 1.0]  # Purple-ish
                    elif style == "cyberpunk":
                        light_color = random.choice([[1.0, 0.2, 0.5], [0.2, 0.8, 1.0], [0.8, 0.2, 1.0]])  # Neon
                    
                    obj["light"] = {
                        "color": light_color,
                        "intensity": 0.7,
                        "range": 5.0
                    }
                
                objects.append(obj)
        
        return objects
    
    def save_space(self, space_data: Dict, output_path: str) -> bool:
        """
        Save the generated space to a file.
        
        Args:
            space_data: The generated space data
            output_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(space_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving space: {e}")
            return False
    
    def load_space(self, input_path: str) -> Dict:
        """
        Load a space from a file.
        
        Args:
            input_path: Path to the space file
            
        Returns:
            Dictionary containing the space data
        """
        try:
            with open(input_path, 'r') as f:
                space_data = json.load(f)
            return space_data
        except Exception as e:
            print(f"Error loading space: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    generator = SpaceGenerator()
    
    space = generator.generate_space(
        description="A modern office space with meeting rooms and open work areas",
        size=(50.0, 3.5, 30.0),
        style="modern",
        room_count=5,
        object_density=0.7
    )
    
    generator.save_space(space, "generated_office_space.json")
    print("Office space generated and saved to generated_office_space.json")
