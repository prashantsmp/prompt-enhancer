# app/mock_mcp_server.py

import asyncio
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server named "t2i-server"
mcp = FastMCP("t2i-server")

@mcp.tool()
def generate_image(prompt: str) -> dict:
    """Generates an image from a detailed text prompt.
    
    Args:
        prompt: The detailed prompt describing the image to generate.
        
    Returns:
        A dict containing the image generation status and simulated URL.
    """
    # Simply echo the prompt and return a simulated image URL
    return {
        "status": "success",
        "image_url": "https://storage.googleapis.com/prompt-enhancer-mock-assets/generated_image.png",
        "prompt": prompt
    }

if __name__ == "__main__":
    mcp.run()
